pragma Singleton
import QtQuick

// Single access point for every interface that depends on the Python backend
// (spec §10). QML views import this singleton instead of reaching for the raw
// `chatBackend` / `settingsBackend` / `fileBackend` context properties, so the
// set of backend-dependent interfaces lives in exactly one file.
//
// The context properties are still registered by `app.py`; this singleton only
// re-exposes them under stable, discoverable names. Add a new backend here (and
// in `app.py`) when the UI needs one.
QtObject {
    id: backends

    // Chat: messages, streaming state, expression/portrait resolution.
    readonly property var chat: chatBackend
    // Settings: theme + character management, persistence.
    readonly property var settings: settingsBackend
    // Read-only filesystem browser used to pick character images.
    readonly property var filesystem: fileBackend
}
