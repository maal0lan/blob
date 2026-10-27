# Issue: Enhanced file access support

## Type
feature / file-access / tools

## Summary
Expand read-only local file access beyond the current narrow intent set: full-text search, more file types, larger file handling, and better folder management.

## Current state
`FolderTools` (`crystal_agent/tools.py`) supports:
- List (top-level of first allowed folder)
- Search (filename-only, case-insensitive substring)
- Read (quoted path, text suffixes only, 2 MB limit, 120k char cap)

Access is opt-in per folder via `file_access_enabled`. Search is filename-only, not full-text.

## Desired outcome
- Full-text search within files (not just filenames)
- Support additional text-based file types
- Configurable/increased file size limits with chunked reading
- Folder browse improvements (nested selection, recent folders)
- File preview in chat with syntax-aware rendering
- Better error messaging for access-denied / oversized / binary files

## Related files
- `crystal_agent/tools.py` — `FolderTools.list_files`, `search_files`, `read_file`
- `crystal_agent/agent.py` — `OllamaAgent._maybe_use_file_tool` intent regexes
- `crystal_agent/config.py` — `Settings.max_file_mb`, `Settings.max_context_chars`, `Settings.allowed_folders`
- `README.md` — folder permissions and local tools section
- `ARCHITECTURE.md` — future tool-call contract
