# Companion Framework — Runtime Flows

Sequence and activity diagrams for the critical scenarios. All diagrams are Mermaid and
render in GitHub, GitLab, Obsidian, and editors with Mermaid support.

Contents:

1. [Startup & composition](#1-startup--composition)
2. [Sending a prompt (write message)](#2-sending-a-prompt-write-message)
3. [Streaming a reply (SSE)](#3-streaming-a-reply-sse)
4. [Loading a previous chat](#4-loading-a-previous-chat)
5. [Creating / editing a bot (character)](#5-creating--editing-a-bot-character)
6. [Switching the active character](#6-switching-the-active-character)
7. [Theme management](#7-theme-management)
8. [Choosing a portrait image (file browser)](#8-choosing-a-portrait-image-file-browser)
9. [Error handling & fallbacks](#9-error-handling--fallbacks)

---

## 1. Startup & composition

The composition root is the single place where dependencies are assembled. The desktop
UI and the FastAPI adapter share the exact same `GfPipeline`.

```mermaid
flowchart TD
    A[Entry point] --> B{Adapter?}
    B -->|Desktop UI| C[ui.app.run]
    B -->|FastAPI| D[main.py lifespan]

    C --> C1{--demo flag?}
    C1 -->|yes| C2[DemoRoot: offline fake pipeline]
    C1 -->|no| E[CompositionRoot config]

    D --> E

    E --> F[Select character = config.characters 0]
    F --> G{Characters empty?}
    G -->|yes| G1[raise ConfigError]
    G -->|no| H[LLMProviderFactory.create_provider]

    H --> I[DatabaseFactory.create]
    I --> J[AIController + DatabaseController]
    J --> K[ConversationWindowProvider + MemoryManager]
    K --> L[ExpressionManager]
    L --> M[GfPipeline built]

    C2 --> N[Start AsyncWorker asyncio thread]
    M --> N
    M --> O[FastAPI: pipeline.init and store in app.state]

    N --> P[Create backends + ThemeController]
    P --> Q[Load Main.qml / enter Qt loop]
    O --> R[Serve requests]
```

**Key points**

- Factories are called **only** in the composition root (`src/ai_girlfriend/composition_root.py`).
- The pipeline is created lazily on demand for the UI and once at startup for FastAPI.
- `invoke demo` swaps the real root for `DemoRoot`, which returns a `DemoPipeline` with no
  network or disk.

---

## 2. Sending a prompt (write message)

The core path for a normal (non-streaming) turn. The QML UI calls
`ChatBackend.sendMessage`, which submits the coroutine to the `AsyncWorker`; the GUI
thread is never blocked.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant QML as ChatView.qml
    participant CB as ChatBackend
    participant W as AsyncWorker
    participant P as GfPipeline
    participant MM as MemoryManager
    participant CP as ConversationWindowProvider
    participant AC as AIController
    participant LLM as ILLMProvider
    participant DB as DatabaseController
    participant EM as ExpressionManager

    User->>QML: type text + Enter
    QML->>CB: sendMessage(text)
    CB->>CB: emit messageAppended("user", text)
    CB->>CB: set busy = true
    CB->>W: submit(pipeline.chat(text, chat_id))
    Note over W: runs on asyncio loop (own QThread)

    P->>P: init() if needed
    P->>MM: _ensure_chat(chat_id)
    alt no chat_id (new conversation)
        MM->>DB: create_chat()
        DB-->>MM: chat_id (UUID)
    else existing chat
        MM-->>P: chat_id
    end

    P->>MM: build_context(chat_id, user_message)
    MM->>CP: build_context(query, chat_id)
    CP->>DB: get_recent_messages(chat_id, window)
    DB-->>CP: recent messages
    CP-->>MM: ContextBundle(messages, memories=[])
    MM-->>P: ContextBundle

    P->>P: _build_request(history + user message)
    Note right of P: system prompt from CharacterInfo,<br/>params from generation_params()

    P->>AC: generate(request)
    AC->>LLM: generate(request) (with timeout)
    LLM-->>AC: GenerationResponse(content)
    AC-->>P: GenerationResponse

    P->>P: _parse_response(content) -> (text, emotion?)
    P->>EM: resolve(emotion)
    EM-->>P: validated expression id

    P->>MM: record_exchange(user_msg, bot_msg)
    MM->>DB: save_exchange(...) (single transaction)
    DB-->>MM: ok
    P-->>W: CharacterResponse(text, expression, chat_id)
    W-->>CB: future done
    CB->>CB: set busy = false
    CB->>QML: messageAppended("assistant", text)
    CB->>QML: expressionChanged(expression)
    QML->>User: render bubble + update portrait
```

**Failure branch**

```mermaid
flowchart TD
    A[chat requested] --> B[build context]
    B --> C[AIController.generate]
    C --> D{Success?}
    D -->|timeout| E[GenerationTimeoutError]
    D -->|provider error| F[ProviderError]
    D -->|ok| G[_parse_response]
    G --> H{JSON valid?}
    H -->|yes| I[text + emotion]
    H -->|no| J[raw text, emotion=None]
    J --> K[ExpressionManager.resolve -> fallback]
    I --> K
    K --> L[save_exchange]
    L --> M{DB write ok?}
    M -->|yes| N[CharacterResponse returned]
    M -->|no| O[StorageError; rollback]
    E --> P[Nothing saved; error surfaced]
    F --> P
    O --> P
```

---

## 3. Streaming a reply (SSE)

Used by `POST /chat/{chat_id}/stream`. The exchange is persisted **only** on the `Done`
event; partial text from a cancelled stream is not saved.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as FastAPI /chat/{id}/stream
    participant P as GfPipeline
    participant AC as AIController
    participant LLM as ILLMProvider (Ollama/DeepSeek)
    participant MM as MemoryManager

    Client->>API: POST message
    API->>P: stream_chat(message, chat_id)
    P->>P: build context + request
    P->>AC: stream(request)
    AC->>LLM: stream(request)
    loop each chunk
        LLM-->>AC: TextDelta(text)
        AC-->>P: TextDelta
        P-->>API: TextDelta
        API-->>Client: event: delta
    end

    alt generation completed
        LLM-->>AC: Done(usage)
        AC-->>P: Done
        P->>P: join collected text + parse
        P->>MM: record_exchange(user, bot)
        P-->>API: Done
        API-->>Client: event: done
    else failure
        LLM-->>AC: Error(message, code)
        AC-->>P: Error
        P-->>API: Error
        API-->>Client: event: error
        Note over P: nothing persisted
    end
```

**Client cancellation:** if the client disconnects mid-stream, the async generator stops;
the `Done` branch never runs and the exchange is not saved.

---

## 4. Loading a previous chat

`ChatHistoryView.qml` lists stored chats and reopens one. The `ChatBackend` retargets its
active `chat_id` to the loaded conversation so subsequent messages continue it.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant HV as ChatHistoryView.qml
    participant CB as ChatBackend
    participant W as AsyncWorker
    participant P as GfPipeline
    participant DB as DatabaseController

    HV->>CB: listChats(50) (on open)
    CB->>W: submit(pipeline.list_chats(50))
    W->>P: list_chats(50)
    P->>DB: list_chats(50)
    DB-->>P: [ChatSummary]
    P-->>W: [ChatSummary]
    W-->>CB: future done
    CB-->>HV: chatsListed([{id, preview, count, updated}])

    User->>HV: tap a conversation
    HV->>CB: loadChat(chat_id)
    CB->>W: submit(pipeline.get_messages(chat_id))
    W->>P: get_messages(chat_id)
    P->>DB: get_messages(chat_id)
    DB-->>P: [Message]
    P-->>W: [Message]
    W-->>CB: future done
    CB->>CB: _chat_id = UUID(chat_id)
    CB-->>HV: chatLoaded(chat_id, transcript)
    HV->>HV: adoptTranscript(); pop back to chat
```

```mermaid
flowchart TD
    A[open history] --> B[listChats]
    B --> C{Any chats?}
    C -->|no| D[show empty state]
    C -->|yes| E[render list]
    E --> F[user selects chat]
    F --> G[loadChat]
    G --> H[pipeline.get_messages]
    H --> I[chatLoaded transcript]
    I --> J[replace transcript + continue conversation]
```

---

## 5. Creating / editing a bot (character)

Characters are edited in `CharacterEditor.qml`. Built-in characters come from
`config.json`; user characters are persisted to `characters.json` through
`CharacterStore`. After saving, `SettingsBackend` rebuilds the pipeline asynchronously.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CE as CharacterEditor.qml
    participant SB as SettingsBackend
    participant CS as CharacterStore
    participant W as AsyncWorker
    participant CR as CompositionRoot
    participant CB as ChatBackend
    participant FS as FileSystemBackend

    User->>CE: fill name/personality/greeting/tuning
    opt add expression image
        User->>CE: click browse
        CE->>FS: listDir(path)
        FS-->>CE: [{name, path, isDir, url}]
        CE->>CE: draftPhotos[id] = path
    end

    User->>CE: Save
    CE->>SB: saveCharacter(payload)
    SB->>SB: validate via CharacterInfo(...)
    alt invalid (e.g. empty name)
        SB-->>CE: "" (UI shows error)
    else valid
        SB->>SB: replace / append in _characters
        SB->>CS: _persist_characters() (custom only)
        CS-->>SB: written to characters.json
        SB-->>CE: new character id
        SB->>W: submit(rebuild pipeline in executor)
        W->>CR: build_pipeline(character=info)
        CR-->>W: new GfPipeline
        W-->>SB: future done
        SB->>CB: apply_character(pipeline, info)
        CB->>CB: reset chat_id, greeting, portrait
        SB-->>CE: charactersChanged / characterChanged
        CE->>CE: pop back
    end
```

```mermaid
flowchart TD
    A[open editor] --> B{Editing existing?}
    B -->|yes| C[prefill from characterInfo]
    B -->|no| D[blank template]
    C --> E[user edits fields]
    D --> E
    E --> F[Save]
    F --> G{name non-empty + valid?}
    G -->|no| H[error snack; stay]
    G -->|yes| I[update in-memory list]
    I --> J{built-in or custom?}
    J -->|custom| K[persist to characters.json]
    J -->|built-in| L[in-memory only]
    K --> M[rebuild pipeline async]
    L --> M
    M --> N[apply to ChatBackend: fresh chat]
    N --> O[pop to chat]
```

**Delete:** custom characters can be deleted (`deleteCharacter`); built-in characters
cannot and the UI shows a message.

---

## 6. Switching the active character

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CP as CharacterPicker.qml
    participant SB as SettingsBackend
    participant W as AsyncWorker
    participant CR as CompositionRoot
    participant CB as ChatBackend
    participant QML as ChatView.qml

    User->>CP: select character
    CP->>SB: selectCharacter(character_id)
    SB->>SB: set busy = true
    SB->>W: submit(rebuild pipeline in executor)
    W->>CR: build_pipeline(character)
    CR-->>W: new GfPipeline
    W-->>SB: _on_built(future, id)
    SB->>CB: apply_character(pipeline, info)
    CB->>CB: fresh chat_id; emit characterChanged
    SB-->>QML: characterChanged -> clear transcript
    SB->>SB: set busy = false
```

---

## 7. Theme management

Themes are role-based Material 3 tokens. Built-in themes are in `ui/themes.py`; custom
themes are validated and persisted by `ThemeStore` to `themes.json`.

```mermaid
flowchart TD
    A[Settings: theme section] --> B{Action}
    B -->|select| C[selectTheme id]
    C --> D[ThemeController.setTheme]
    D --> E[emit themeChanged -> QML colors update]

    B -->|create/edit| F[ThemeEditor: fill token map]
    F --> G[SettingsBackend.saveTheme]
    G --> H[ThemeController.saveCustomTheme]
    H --> I{building a built-in id?}
    I -->|yes| J[reject: return '']
    I -->|no| K[ThemeStore.validate]
    K --> L{valid tokens?}
    L -->|no| M[reject: return '']
    L -->|yes| N[merge + mark custom]
    N --> O[persist to themes.json]
    O --> P[setTheme + emit themesChanged]

    B -->|delete| Q[deleteCustomTheme id]
    Q --> R{custom theme?}
    R -->|no| S[refuse]
    R -->|yes| T[remove + persist + fallback to default]
```

---

## 8. Choosing a portrait image (file browser)

QML's platform `FileDialog` is not always available, so an in-app read-only browser is
used instead (`FileSystemBackend` + `FileBrowser.qml`).

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CE as CharacterEditor.qml
    participant FB as FileBrowser.qml
    participant FS as FileSystemBackend

    User->>CE: click browse (target = expr id or new row)
    CE->>FB: open()
    FB->>FS: listDir(cwd)
    FS-->>FB: dirs + image files
    User->>FB: navigate / select image
    FB->>FS: setCwd(path) (on folder enter)
    FB-->>CE: applyBrowsedFile(path)
    CE->>CE: set draftPhotos[target] = path
```

Only directories and known image suffixes are listed; unreadable directories yield an
empty list instead of raising.

---

## 9. Error handling & fallbacks

```mermaid
flowchart TD
    subgraph Core
      E1[CompanionError] --> E2[ProviderError]
      E2 --> E3[GenerationTimeoutError]
      E1 --> E4[StorageError]
      E1 --> E5[ConfigError]
      E1 --> E6[InvalidExpressionError]
    end

    subgraph FastAPI
      F1[GenerationTimeoutError -> 504]
      F2[ProviderError -> 502]
      F3[StorageError -> 500]
      F4[ConfigError -> 500]
    end

    subgraph DesktopUI
      U1[errorRaised signal -> Snackbar]
      U2[portrait fallback chain -> emoji placeholder]
      U3[missing asset -> 'Missing asset' text]
    end

    E3 --> F1
    E2 --> F2
    E4 --> F3
    E5 --> F4
    E1 --> U1
    E6 --> U2
```

**Portrait fallback resolution** (`ChatBackend._expression_url`): walk candidates —
the requested id → `initial_expression` → `default` → any mapped asset — and return the
first image that exists on disk; otherwise return `''` so QML shows the emoji placeholder.

**Reliability guarantees**

- A generation failure saves nothing (no half exchange).
- Streaming persists only on `Done`.
- `InvalidExpressionError` never maps to an arbitrary filesystem path (assets are
  resolved through `ExpressionManager` with a `..` traversal guard).
- Custom character/theme files that are malformed are skipped rather than crashing the
  app.
