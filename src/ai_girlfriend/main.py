"""FastAPI transport adapter.

A thin adapter: it validates the HTTP request, calls ``GfPipeline``, and
translates domain errors into HTTP responses. No business logic lives here
(see spec, section 10). The pipeline is built once in ``lifespan`` and stored in
the app state as a singleton.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from src.ai_girlfriend.composition_root import CompositionRoot
from src.ai_girlfriend.config.config import config
from src.ai_girlfriend.exc import (
    CompanionError,
    ConfigError,
    GenerationTimeoutError,
    ProviderError,
    StorageError,
)
from src.ai_girlfriend.gf_pipeline import GfPipeline
from src.ai_girlfriend.models.events import Done, TextDelta
from src.ai_girlfriend.models.events import Error as ErrorEvent


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Build the pipeline singleton and store it in the app state on startup."""
    pipeline: GfPipeline = CompositionRoot(config).build_pipeline()
    await pipeline.init()
    app.state.pipeline = pipeline
    try:
        yield
    finally:
        await pipeline.close()


app = FastAPI(
    title="AI Girlfriend API",
    description="An API for the AI Girlfriend application.",
    version="0.0.1",
    default_response_class=JSONResponse,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """Payload for sending a message."""

    message: str = Field(min_length=1, description="The user's message.")


def get_pipeline(request: Request) -> GfPipeline:
    """Return the pipeline singleton stored in the app state."""
    pipeline = getattr(request.app.state, "pipeline", None)
    if pipeline is None:  # pragma: no cover - only during startup failure
        raise HTTPException(status_code=503, detail="Pipeline is not initialized.")
    return pipeline


def _translate_error(exc: CompanionError) -> HTTPException:
    """Map a domain error to an HTTP status (see spec, section 6.5)."""
    if isinstance(exc, GenerationTimeoutError):
        return HTTPException(status_code=504, detail=str(exc))
    if isinstance(exc, ProviderError):
        return HTTPException(status_code=502, detail=str(exc))
    if isinstance(exc, StorageError):
        return HTTPException(status_code=500, detail=str(exc))
    if isinstance(exc, ConfigError):
        return HTTPException(status_code=500, detail=str(exc))
    return HTTPException(status_code=500, detail=str(exc))


@app.get(path="/", summary="Root Endpoint", description="Returns a welcome message.")
async def root() -> JSONResponse:
    """Root endpoint that returns a welcome message."""
    return JSONResponse(content={"message": "Welcome to the AI Girlfriend API!"})


@app.post(
    path="/chat",
    summary="Chat Endpoint",
    description="Sends a message when no chat id exists yet (new conversation).",
)
async def create_chat(request: Request, payload: ChatRequest) -> JSONResponse:
    """Start a new conversation with a first message."""
    pipeline = get_pipeline(request)
    try:
        response = await pipeline.chat(payload.message)
    except CompanionError as exc:
        raise _translate_error(exc) from exc
    return JSONResponse(
        content={"text": response.text, "expression": response.expression}
    )


@app.post(
    path="/chat/{chat_id}/message",
    summary="Send Message Endpoint",
    description="Sends a message in an existing chat session.",
)
async def send_message(
    request: Request, chat_id: UUID, payload: ChatRequest
) -> JSONResponse:
    """Send a message within an existing conversation."""
    pipeline = get_pipeline(request)
    try:
        response = await pipeline.chat(payload.message, chat_id=chat_id)
    except CompanionError as exc:
        raise _translate_error(exc) from exc
    return JSONResponse(
        content={"text": response.text, "expression": response.expression}
    )


@app.get(
    path="/chat/{chat_id}",
    summary="Get Chat Endpoint",
    description="Retrieves information about a specific chat session.",
)
async def get_chat(request: Request, chat_id: UUID) -> JSONResponse:
    """Return basic metadata and the stored history of a chat session."""
    pipeline = get_pipeline(request)
    messages = await pipeline.memory_manager.database.get_recent_messages(
        chat_id, limit=config.context_window
    )
    return JSONResponse(
        content={
            "chat_id": str(chat_id),
            "character": pipeline.gf_config.name,
            "messages": [
                {
                    "id": str(m.id),
                    "role": m.role.value,
                    "content": m.content,
                    "created_at": m.created_at.isoformat(),
                }
                for m in messages
            ],
        }
    )


@app.post(
    path="/chat/{chat_id}/stream",
    summary="Stream Message Endpoint",
    description="Streams the assistant's reply as Server-Sent Events.",
)
async def stream_message(
    request: Request, chat_id: UUID, payload: ChatRequest
) -> StreamingResponse:
    """Stream a reply built from the typed ``StreamEvent`` contract."""
    pipeline = get_pipeline(request)

    async def event_source() -> AsyncIterator[str]:
        try:
            async for event in pipeline.stream_chat(payload.message, chat_id=chat_id):
                if isinstance(event, TextDelta):
                    yield f"event: delta\ndata: {event.text}\n\n"
                elif isinstance(event, Done):
                    yield "event: done\ndata: {}\n\n"
                elif isinstance(event, ErrorEvent):
                    yield f"event: error\ndata: {event.message}\n\n"
        except CompanionError as exc:
            yield f"event: error\ndata: {exc}\n\n"

    return StreamingResponse(event_source(), media_type="text/event-stream")
