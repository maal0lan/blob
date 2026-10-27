# History and Persistence — Crystal Companion

## Where data lives

All app data is stored under `%APPDATA%\CrystalCompanion\` (resolves to the user's AppData/Roaming directory on Windows). The directory is created automatically on first use.

| File | Purpose |
|---|---|
| `settings.json` | Persistent user preferences (atomic write via `.tmp` + replace) |
| `history.sqlite3` | Conversation history (SQLite) |
| `crystal.log` | Rotating diagnostics log (2 MB max, 4 backups) |

## Settings (`crystal_agent/config.py`)

The `Settings` dataclass holds all user-configurable values.

- **`load()`** — reads `settings.json`, filters to known dataclass fields, falls back to defaults on missing/corrupt file
- **`save()`** — writes atomically: serializes to a `.tmp` file, then replaces `settings.json`

Settings are edited in the Settings window and saved when the user clicks "Save settings". Some fields are stored for future extension and don't yet drive distinct features (`max_context_chars`, `show_debug_panel`, `speak_errors`).

## Conversation history (`crystal_agent/history.py`)

SQLite database with two tables:

```sql
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Functions

| Function | Behavior |
|---|---|
| `connect()` | Creates app-data dir, opens SQLite with 10s timeout, enables foreign keys |
| `initialize()` | Creates tables if not exist |
| `add(session_id, role, content)` | Inserts a message; session title is auto-set from first user message (first line, max 70 chars); skips empty content |
| `recent(session_id, limit=12)` | Returns last N messages as `{"role", "content"}` dicts, oldest first |
| `clear()` | Deletes all sessions |

History is controlled by the `remember_history` setting. When disabled, the chat still works but doesn't persist messages. Disabling persistence does **not** delete previous history — remove the database file only after quitting the app if you want to erase it.

## Logging (`crystal_agent/logging_setup.py`)

- Rotating file handler: `crystal.log`, 2 MB per file, 4 backup files, UTF-8
- Stream handler: console output
- Format: `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`
- Log level configurable via `log_level` setting (default `DEBUG`)
- Logger name: `"crystal"`

## Related notes

- [[configuration-reference]] — all settings and their defaults
- [[module-map]] — `config.py`, `history.py`, `logging_setup.py` locations
- [[security-and-privacy]] — history stored locally, log privacy considerations
- [[setup-and-deployment]] — where app-data is created