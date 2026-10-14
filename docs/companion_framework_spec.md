# AI Girlfriend / Companion Framework — Architecture Specification

**Status:** implementation-aligned specification, revision 3
**Implementation language:** Python (>= 3.13)
**Main technologies:** Pydantic / pydantic-settings, `typing.Protocol`, SQLite (`aiosqlite`), httpx, Ollama & OpenAI-compatible HTTP APIs, FastAPI, PySide6/Qt (QML)
**Development tooling:** Poetry, invoke, pytest, ruff, pre-commit

> This document describes the system **as implemented**. The class diagram lives in
> [`companion_class_diagram.mmd`](./companion_class_diagram.mmd) and the runtime
> scenarios (prompt, streaming, chat loading, bot creation, startup) live in
> [`flows.md`](./flows.md).

## What changed compared to revision 2

Revision 2 was an architecture **proposal**; the codebase has since diverged. This
revision records the deltas so the docs match the code:

- The project is packaged as `ai_girlfriend` (package root `src/ai_girlfriend`).
- **Configuration** is a single `Config` (pydantic-settings) read from `config.json`;
  it also embeds the list of characters as `CharacterInfo` models. `Settings` and a
  separate `GfConfig` class no longer exist.
- **Character** model is `CharacterInfo`; the spec-facing accessors `character_id`,
  `system_prompt`, `expressions`, `available_emotions` and `generation_params()` are
  derived properties/methods, not separate fields.
- **LLM** contracts live in `models/llm.py` (`ILLMProvider`, `GenerationRequest`,
  `GenerationResponse`, `Message`, `Role`); the factory is `LLMProviderFactory`
  (methods `create_provider`), and concrete providers are `OllamaProvider` and
  `DeepSeekProvider` (no `OpenAICompatibleProvider`).
- **Storage** contract keeps its low-level name `IDatabaseStorage` (not
  `IDatabaseProvider`); the table key is `chat_id`, and the provider exposes
  `create_chat`, `save_message`, `save_exchange`, `get_recent_messages`,
  `list_chats`, `get_messages`.
- **Context** contract is `IContextProvider.build_context(query, chat_id)`; the default
  provider is `ConversationWindowProvider`.
- **Pipeline lifecycle** uses `init()` / `close()` (not `initialize()`). `chat()` and
  `stream_chat()` accept an optional `chat_id: UUID | None` and lazily create a chat.
- The public facade gained read-only history helpers: `list_chats()` and
  `get_messages()`.
- **Transport** is the FastAPI adapter in `main.py` with four endpoints
  (`/chat`, `/chat/{chat_id}/message`, `/chat/{chat_id}`, `/chat/{chat_id}/stream`).
- The **desktop UI** is a QML/PySide6 application (`ui/`) with an `AsyncWorker`
  QThread bridge, `ChatBackend` / `SettingsBackend` / `FileSystemBackend` QObjects,
  and a theme + character persistence layer (`ThemeStore`, `CharacterStore`).
- The widget-based adapter (`ui_builder/`) is a secondary, simpler Qt path; the QML
  UI is the primary desktop experience.
- **Streaming contract** is a Pydantic discriminated union in `models/events.py`
  (`TextDelta | Done | Error`).

## 1. Project Goal

The project is an independent Python library for building personal AI companions and
local AI assistants. The primary scenario is a character with its own prompt, dialogue
history, and visual emotions. The core is reusable through different interfaces
(currently FastAPI and a Qt/QML desktop app) and must not depend on any of them.

### Goals

- Separate domain logic, configuration, providers, and interfaces.
- Support swapping LLM and database providers through stable contracts.
- Store dialogue history and reserve space for long-term memory and RAG.
- Separate the character's state/emotion from the text generation mechanism.
- Allow the core to be used without a graphical interface.
- Support testing components through substitutable implementations of the contracts.
- Reserve minimal room for the tools of a future local assistant.

### Non-goals of the first version

- Autonomous execution of arbitrary operating system commands.
- Mandatory RAG integration before the first MVP.
- Implementing assistant tools (the MVP has only a placeholder contract).
- Permanent lock-in to a single LLM provider, a single GUI, or a single config format.

## 2. Architectural Principles

1. **The core does not depend on the UI.** Qt/FastAPI import the core; the core never
   imports them (`import PySide6` / `import fastapi` are forbidden in the core).
2. **Dependencies point inward.** Domain models and contracts do not depend on concrete
   adapters.
3. **Providers are adapters.** `OllamaProvider` / `DeepSeekProvider` implement
   `ILLMProvider`; `SQLiteProvider` implements `IDatabaseStorage`.
4. **Factories create, controllers use.** Factories are called only in the composition
   root. Controllers receive ready-made providers through their constructors.
5. **The pipeline is a facade, not a "god object".** It coordinates services and
   lifecycle but contains no SQL, HTTP, or Qt/QML logic.
6. **Configuration is split by purpose in one source.** Global runtime settings and
   character profiles share one `config.json`, but map to distinct models
   (`Config` vs `CharacterInfo`).
7. **RAG is an optional context adapter.** The base scenario uses a window of recent
   messages.
8. **Asynchronous operations do not block the UI.** Blocking work runs on an asyncio
   loop in its own thread (`AsyncWorker`); the Qt event loop is never blocked.
9. **Errors are typed.** Providers raise domain errors; adapters translate them at
   their own level.
10. **Abstraction only for a real point of substitution.**

## 3. Class Diagram

See [`companion_class_diagram.mmd`](./companion_class_diagram.mmd) (Mermaid). It renders
in GitHub, GitLab, Obsidian, and editors with Mermaid support.

### Notes on the diagram

- The diagram shows logical roles and the principal operations, not exact signatures.
- `DatabaseController` remains a separate application-layer boundary over
  `IDatabaseStorage`. It currently mostly forwards calls; if it stays a pure
  pass-through it may be merged into the provider (principle 10).
- `MemoryManager` depends on `DatabaseController` and `IContextProvider`, never on
  `SQLiteProvider`.
- `GfPipeline` does not create its own dependencies; `CompositionRoot` assembles them.
- `FakeLLMProvider` and `InMemoryDatabaseProvider` ship inside the package
  (`ai_girlfriend.testing`) so tests and the demo need no network or disk.

## 4. Layers and Dependency Rules

| Layer | Contents | May import |
|---|---|---|
| `models` (domain) | `Message`, `Role`, `GenerationRequest/Response`, `StreamEvent`, `ContextBundle`, `Memory`, `CharacterInfo`, `CharacterResponse`, `Chat`, `ChatSummary`, contracts (`ILLMProvider`, `IDatabaseStorage`, `IContextProvider`) | stdlib, Pydantic |
| `config` | `Config`, `.env`/`config.json` loading | `models` |
| application | `GfPipeline`, `AIController`, `DatabaseController`, `MemoryManager`, `ExpressionManager` | `models`, `config` |
| providers | `OllamaProvider`, `DeepSeekProvider`, `SQLiteProvider`, `ConversationWindowProvider` | `models`, third-party libraries |
| factories + bootstrap | `LLMProviderFactory`, `DatabaseFactory`, `CompositionRoot` | everything above |
| `adapters` | `main.py` (FastAPI), `ui/` (QML), `ui_builder/` (widgets) | the core's public API |
| `exc` | domain error hierarchy | — |

These rules are enforced by keeping UI/FastAPI imports out of the core packages.

## 5. Configuration Models

### 5.1 `Config` (`config/config.py`)

Built on `pydantic-settings`, loaded from `config.json` at the project root (also
readable from environment variables, which take precedence for the same key). It holds
global startup and infrastructure parameters:

- LLM: `provider` (`ollama` | `deepseek`), `llm_url`, `model`, `api_key`;
- generation: `context_window`, `request_timeout`, `temperature`, `max_tokens`;
- database: `database_provider` (`sqlite` | `postgresql`), `database_url`;
- `characters: list[CharacterInfo]`.

`api_key` is stored as `SecretStr` and is never logged. A module-level `config = Config()`
singleton is imported by the adapters and the composition root.

### 5.2 `CharacterInfo` (`models/character.py`)

Responsible for a single character profile:

- `name`, `personality`, `greeting_message`;
- `photo_emoji_map: dict[str, str]` — expression id → asset path;
- `initial_expression`;
- optional per-character `temperature` and `max_tokens` (override the global config);
- `schema_version`.

Derived accessors keep the core independent of the raw config shape:
`character_id` (slug from `name`), `expressions` (non-empty entries only),
`available_emotions`, `system_prompt`, and `generation_params(...)`.

Asset paths are validated at load time: absolute (or `~`) paths are allowed as-is;
relative paths must not escape the character directory with `..`.

## 6. Contracts and Providers

### 6.1 LLM

`ILLMProvider` (a `runtime_checkable` Protocol in `models/llm.py`) receives a normalized
`GenerationRequest` and returns a `GenerationResponse` or streams `StreamEvent`s.
`LLMProviderFactory.create_provider(...)` maps `provider_name` to a concrete class
(`ollama` → `OllamaProvider`, `deepseek` → `DeepSeekProvider`) and raises
`ProviderError` for unknown names or a missing API key.

`OllamaProvider` talks to the local `/api/chat` endpoint over `httpx` (no `ollama` SDK),
including the NDJSON streaming protocol. `DeepSeekProvider` talks to an
OpenAI-compatible `/chat/completions` endpoint (SSE streaming). Both translate client
errors into `GenerationTimeoutError` / `ProviderError`.

**Streaming contract.** `stream()` yields `TextDelta(text)`, then `Done(usage, metadata)`
on success, or `Error(message, code)` on failure. One contract serves both the FastAPI
SSE endpoint and the Qt streaming path.

**Emotion handling.** The character's `system_prompt` asks the model to reply with a
strict JSON object `{"text": ..., "emotion": ...}`; `GfPipeline._parse_response()`
extracts `text` and an optional expression (accepting the legacy `expression` key). If
parsing fails, the raw text is used and the expression falls back. The expression is
always validated against `CharacterInfo.expressions` — the model can never resolve an
arbitrary filesystem path.

### 6.2 Database

`IDatabaseStorage` (Protocol in `models/database.py`) provides consistent operations:
`create_chat`, `save_message`, **atomic `save_exchange`**, `get_recent_messages`,
`list_chats`, `get_messages`, `close`. SQL and transactions live only in `SQLiteProvider`.

`DatabaseController` wraps the provider behind the same provider-agnostic surface.
`DatabaseFactory.create(provider, url)` normalizes `sqlite:///path` into a filesystem
path and currently supports only `sqlite` (raising `ConfigError` otherwise).

`sqlite3` blocking is avoided by using `aiosqlite`. `save_exchange` writes the user and
assistant messages inside a single transaction, so a failed generation never leaves a
half-saved exchange.

### 6.3 Context

`IContextProvider.build_context(query, chat_id)` returns a `ContextBundle` with separate
fields `messages` (history) and `memories` (retrieved memories). The default
`ConversationWindowProvider` returns the last `context_window` messages and no memories.

### 6.4 Tools (placeholder)

`agent/tools.py` currently defines only stubs (`ITool`, `ToolRegistry`) — the local
assistant is post-MVP. Future tools will use explicit permissions, user confirmation,
and argument validation.

### 6.5 Errors

`CompanionError` is the base; descendants are `ProviderError`
(→ `GenerationTimeoutError`), `StorageError`, `ConfigError`, `InvalidExpressionError`.
Providers convert library exceptions into these types; `AIController` adds timeouts and
retries; adapters map them to HTTP statuses (see §10) or UI messages.

## 7. Factories and the Composition Root

`LLMProviderFactory` and `DatabaseFactory` create providers from `Config`. The single
assembly point is `CompositionRoot(config).build_pipeline(character=None)`:

1. pick the character (defaults to `config.characters[0]`, raising `ConfigError` if
   none are configured);
2. factories create an `ILLMProvider` and an `IDatabaseStorage`;
3. wrap them in `AIController` and `DatabaseController`;
4. build a `ConversationWindowProvider` and `MemoryManager`;
5. build an `ExpressionManager`;
6. return a ready `GfPipeline` carrying `default_temperature` / `default_max_tokens`.

In tests the same pipeline is assembled manually from `FakeLLMProvider` and
`InMemoryDatabaseProvider`.

## 8. Message Processing Flow

See [`flows.md`](./flows.md) for the full flowcharts/sequence diagrams.

`GfPipeline.chat()`:

1. Lazily `init()` the pipeline (initializes the database).
2. `_ensure_chat(chat_id)` — reuse the given chat id or create a new chat row so
   messages' foreign key exists.
3. Ask `MemoryManager.build_context()` for the recent history via
   `IContextProvider`.
4. Build a `GenerationRequest`: the character `system_prompt`, the context, and the user
   message; params come from `CharacterInfo.generation_params()` (character overrides beat
   global defaults; the token cap maps to `num_predict` for Ollama or `max_tokens`
   otherwise).
5. `AIController.generate()` calls the provider; errors become domain errors.
6. `_parse_response()` normalizes the structured output; `ExpressionManager.resolve()`
   validates the expression id (fallback chain → `initial_expression`).
7. `MemoryManager.record_exchange()` saves both messages in one transaction.
8. Return a `CharacterResponse(text, expression, chat_id)`.

`stream_chat()` mirrors this but yields `StreamEvent`s and saves the exchange only on
`Done`. Partial text from a cancelled stream is **not** persisted.

Reliability rules:

- On generation failure nothing is saved (no false exchange).
- Messages carry UUID identifiers.
- In streaming mode the exchange is saved on `Done`.

## 9. RAG and Memory

RAG is not a mandatory dependency. It plugs in through `IContextProvider`; the external
RAG project would be wrapped by an `RAGContextProvider` and distributed as a separate
optional package. `GfPipeline` history reads (`list_chats`, `get_messages`) and the
UI history view are already implemented on top of the storage layer.

The system logically distinguishes:

1. **Dialogue history** — the message sequence of a conversation.
2. **Long-term memory** — facts/events that outlive the short context.
3. **RAG retrieval** — finding relevant fragments for the current query.

`ContextBundle` keeps `messages` and `memories` separate.

## 10. Transport Adapters

All adapters live outside the core packages and use the core's public API (`GfPipeline`).

### FastAPI (`main.py`)

A thin transport adapter. The pipeline is built once in `lifespan` and stored in
`app.state` as a singleton. Domain errors are mapped to HTTP statuses:
`GenerationTimeoutError → 504`, `ProviderError → 502`, `StorageError → 500`,
`ConfigError → 500`.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/` | Welcome message. |
| `POST` | `/chat` | New conversation: send the first message (no chat id). |
| `POST` | `/chat/{chat_id}/message` | Send a message in an existing chat. |
| `GET` | `/chat/{chat_id}` | Chat metadata + stored history. |
| `POST` | `/chat/{chat_id}/stream` | Stream the reply as Server-Sent Events. |

### Qt (desktop)

Two paths exist:

- **QML UI (`ui/`)** — the primary experience. `run()` in `ui/app.py` builds the
  `CompositionRoot`, starts an `AsyncWorker` (a `QThread` running its own asyncio loop),
  constructs `ChatBackend` / `SettingsBackend` / `ThemeController` / `FileSystemBackend`,
  registers the `ThemeController` singleton, exposes the backends as context properties,
  and loads `Main.qml`. QML renders; Python holds state; the core does the work. Run it
  with `invoke ui` (real pipeline) or `invoke demo` (offline fake core).
- **Widget adapter (`ui_builder/`)** — a minimal `ChatWindow` + `UIBuilder` +
  `QtDesktopAdapter` using the same `AsyncWorker`, useful for a lightweight or programmatic
  window.

The main rule: no core call blocks the GUI thread. The QML layer reaches the Python
backends through the `Backends` singleton (`ui/qml/Backends.qml`), which re-exposes the
context properties under stable names.

## 11. Repository Structure (as implemented)

```text
ai-girlfriend/
├── pyproject.toml
├── tasks.py                    # invoke tasks
├── config.example.json
├── .env.example
├── config.json                 # local, not committed
├── src/
│   └── ai_girlfriend/
│       ├── __init__.py
│       ├── composition_root.py # CompositionRoot.build_pipeline()
│       ├── config/config.py    # Config (pydantic-settings)
│       ├── exc.py              # domain error hierarchy
│       ├── gf_pipeline.py      # GfPipeline facade
│       ├── main.py             # FastAPI adapter
│       ├── agent/tools.py      # ITool / ToolRegistry stubs
│       ├── character/expression_manager.py
│       ├── database/
│       │   ├── database_controller.py
│       │   ├── database_factory.py
│       │   ├── sqlite_provider.py
│       │   ├── conversation_window.py
│       │   └── memory_manager.py
│       ├── llm/
│       │   ├── llm_provider.py # AIController + LLMProviderFactory
│       │   ├── ollama_provider.py
│       │   └── deepseek_provider.py
│       ├── models/
│       │   ├── llm.py          # Message, Role, requests, ILLMProvider
│       │   ├── events.py       # StreamEvent union
│       │   ├── character.py    # CharacterInfo
│       │   ├── context.py      # ContextBundle, Memory, IContextProvider
│       │   ├── database.py     # Chat, ChatSummary, IDatabaseStorage
│       │   ├── responses.py    # CharacterResponse
│       │   └── agent.py
│       ├── testing/            # FakeLLMProvider, InMemoryDatabaseProvider
│       ├── ui/                 # QML desktop app (primary)
│       │   ├── app.py          # bootstrap
│       │   ├── backends.py     # AsyncWorker, ChatBackend, SettingsBackend
│       │   ├── characters_store.py, themes.py, themes_store.py
│       │   ├── filesystem.py, plugins.py, demo.py
│       │   └── qml/            # Main.qml, ChatView.qml, SettingsView.qml, ...
│       └── ui_builder/         # minimal widget adapter
└── tests/
    ├── unit/
    ├── contract/
    └── integration/
```

Qt and FastAPI are runtime dependencies in the current `pyproject.toml`; the `qt` and
`rag` extras reserve space for optional packaging.

## 12. Development Tooling

The single entry point is `tasks.py` (invoke):

| Task | Effect |
|---|---|
| `invoke format` | `ruff format` + `ruff check --fix` |
| `invoke check` | `ruff check` + `ruff format --check` |
| `invoke test` | `pytest` (with coverage reports) |
| `invoke ci` | `check` then `test` |
| `invoke ui` | Launch the QML UI against the real pipeline |
| `invoke demo` | Launch the QML UI against the offline demo core |

`ruff` is configured in `pyproject.toml` (`line-length = 88`, `target-version = "py313"`,
selects `E/W/F/I/B/UP/N/ASYNC/RUF`, with QML-integration naming relaxations for `ui/`).
`pytest` uses `asyncio_mode = "auto"`, `pythonpath = ["."]`, and markers
`unit` / `contract` / `integration`. Coverage HTML is written to `htmlcov/`.

## 13. Implementation Stages

| Stage | Scope | Status |
|---|---|---|
| 0 | Project skeleton (`pyproject.toml`, `tasks.py`, packages) | done |
| 1 | Contracts, domain models, fakes, facade | done |
| 2 | Vertical slice: `OllamaProvider`, `SQLiteProvider`, factories, contract tests | done |
| 3 | FastAPI adapter (chat, message, history, SSE stream) | done |
| 4 | Character & GUI (QML app, themes, character management, history) | done |
| 5 | RAG (`RAGContextProvider`) | planned |
| 6 | Library packaging, CI, CLI, assistant tools | planned |

## 14. Testing

- **Unit:** composition wiring, response normalization and emotion mapping, expression
  resolution/validation, memory manager, UI stores, Qt adapter, and (via fakes) the
  pipeline without network, disk, or GUI.
- **Contract:** every `IDatabaseStorage` implementation passes one shared suite
  (in-memory + SQLite).
- **Integration:** the SQLite provider with a temporary database.
- **Adapter:** FastAPI/Qt verify only the integration with the core.
- **Failure tests:** unavailable model, timeout, malformed model output, invalid emotion,
  missing asset, database write error.

## 15. MVP Readiness Criteria

- Configuration is loaded and validated from `config.json`.
- Providers are created by factories in the composition root; services depend on
  contracts.
- A message reaches the LLM and returns a normalized `CharacterResponse`.
- History is saved to and restored from SQLite; exchanges are saved atomically.
- `GfPipeline` works in a test without FastAPI and Qt (using fakes).
- The FastAPI adapter and the QML UI consume the same core.
- The absence of RAG does not prevent the base scenario.
- An invalid expression id never leads to arbitrary filesystem access.
- Errors and resource cleanup are predictable; a generation failure leaves no false
  exchange.

## 16. Open Architectural Decisions

- Whether `GfPipeline` remains a specialized companion facade or grows into a universal
  agent (assistant mode + `ToolRegistry`).
- Whether `DatabaseController` stays a separate layer or is merged into the provider.
- Async core ↔ Qt integration: currently a dedicated asyncio thread (`AsyncWorker`); keep
  or evaluate `qasync`.
- Whether to persist partial text when a stream is cancelled.
- Whether RAG is a separate package or an extra of the same distribution.
- Whether Qt and FastAPI become optional extras rather than hard dependencies.
