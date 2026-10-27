# Issue: Data retention / delete-history UI

## Type
security / privacy / ui

## Source
SECURITY.md checklist item: **"Data retention / delete-history UI"** (currently unchecked)

## Summary
Add a data retention and delete-history UI so users can erase stored conversation history and settings.

## Current state
History is stored in SQLite (`%APPDATA%\CrystalCompanion\history.sqlite3`) and settings in JSON (`settings.json`). Turning off `remember_history` stops future persistence but does **not** delete previous history. There is no UI to delete data.

## Desired outcome
- UI button(s) to clear conversation history and/or delete the history database
- Option to delete settings / reset to defaults
- Confirmation dialog before destructive data deletion
- Document that disabling persistence does not erase existing data
- Update SECURITY.md checklist to mark this item complete

## Related files
- `crystal_agent/history.py` — `clear()`, SQLite schema
- `crystal_agent/config.py` — `Settings.save()`, defaults
- `crystal_agent/ui/windows.py` — `SettingsWindow`, `DebugWindow`
- `SECURITY.md` — security checklist
- `README.md` — history/persistence section
