# Companion — QML UI (Material 3)

```bash
pip install PySide6          # Qt >= 6.5
cd src
python -m ai_girlfriend.ui --demo      # offline demo core; type /error to see the snackbar
```

Real core: `from ai_girlfriend.ui.app import run; run(root=composition_root)` where
`root.config.characters` is a list of `CharacterInfo` (character_id, name, personality,
initial_expression, greeting, photo_emoji_map) and `root.build_pipeline(character=...)`
returns an object with `chat(text, chat_id=None)` (sync or async) whose result has
`.text`, `.expression`, `.chat_id`.

pyproject.toml:

```toml
[tool.poetry]
include = ["ai_girlfriend/ui/qml/**/*.qml", "ai_girlfriend/ui/qml/qmldir"]
```
