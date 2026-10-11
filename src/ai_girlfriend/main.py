from collections.abc import Generator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse


def lifespan() -> Generator[None]:
    """
    This function states singleton classes into global state
    """
    yield


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


@app.get(path="/", summary="Root Endpoint", description="Returns a welcome message.")
async def root() -> JSONResponse:
    """
    Root endpoint that returns a welcome message.
    """
    return JSONResponse(content={"message": "Welcome to the AI Girlfriend API!"})


@app.post(
    path="/chat",
    summary="Chat Endpoint",
    description="Endpoint for chatting with the AI Girlfriend.",
)
async def create_chat() -> JSONResponse:
    """
    Creates a new chat session with the AI Girlfriend.
    This endpoint will handle the chat logic and return responses from the AI model.
    """


@app.get(
    path="/chat/{chat_id}",
    summary="Get Chat Endpoint",
    description="Endpoint to retrieve a specific chat session.",
)
async def get_chat(chat_id: str) -> JSONResponse:
    """
    Retrieves a specific chat session by its ID.
    This endpoint will return the chat history and any relevant information about the session.
    """


@app.post(
    path="/chat/{chat_id}/message",
    summary="Send Message Endpoint",
    description="Endpoint to send a message in a specific chat session.",
)
async def send_message(chat_id: str) -> JSONResponse:
    """
    Sends a message in a specific chat session.
    This endpoint will handle sending messages to the AI model and returning the AI's response.
    """
