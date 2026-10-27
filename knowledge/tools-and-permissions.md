# Tools and Permissions — Crystal Companion

## FolderTools (`crystal_agent/tools.py`)

Conservative, read-only local-file tools. No shell, no execution, no arbitrary filesystem access.

## Supported text suffixes

`.txt`, `.md`, `.py`, `.json`, `.csv`, `.log`, `.yaml`, `.yml`, `.toml`, `.ini`, `.html`, `.css`, `.js`, `.ts`, `.sql`, `.xml`

Binary files are rejected by extension. Files above the configured size limit are rejected.

## Path safety

- Folder roots are resolved and validated at `FolderTools` construction time (must exist and be directories)
- `_safe()` canonicalizes paths with `expanduser()` and `resolve()`; relative paths are resolved against each allowed root
- `_is_within_root()` checks that a candidate path equals a root or is a descendant of one
- Any path outside the allowed roots raises `PermissionError`

## Tools

| Tool | Behavior |
|---|---|
| `list_files(folder="", limit=100)` | Lists the top level of a folder (first allowed root if none specified). Sorted: directories first, then case-insensitive name. Capped at 250 items. |
| `search_files(query, limit=30)` | Filename-only search across all allowed roots (rglob). Case-insensitive substring match on filename. Capped at 100 matches. |
| `read_file(path)` | Reads a text file: validates path, checks suffix, checks size limit, returns up to 120,000 chars with `errors="replace"`. |

## File access flow (agent side)

Folder access is **off by default** (`file_access_enabled = false`). To use file tools:

1. User adds folders in Settings → Folder Access and enables the master switch
2. User sends a query matching a narrow explicit intent (list, search, or read a quoted path)
3. `OllamaAgent._maybe_use_file_tool()` detects the intent and calls the matching `FolderTools` method
4. File context is prepended to the Ollama prompt, capped at `max_context_chars`

## Current limitations

- Not a general-purpose agent loop — recognizes a few explicit intents rather than letting the LLM call arbitrary tools
- Search is **filename-only**; no full-text indexing or RAG
- Folder selection is an access boundary, not a substitute for OS permissions — the app runs with the user's Windows account permissions
- Do not add a whole drive or home folder unless you genuinely want to expose its text-file contents
- Read-only only — no file writes, deletes, shell commands, or program execution

## Future tool-call contract (per ARCHITECTURE.md)

Do not parse arbitrary model-generated Python or shell commands. Define a strict JSON schema with a small enum of tool names and validated arguments. Check against a user-configured allowlist, show confirmation for consequential actions, execute with timeouts, cap output, and return structured success/error results. The current code intentionally does not use the uploaded MCP client.

## Tests (`tests/test_tools.py`)

| Test | Covers |
|---|---|
| `test_reads_only_inside_allowed_folder` | Path allowlist enforcement; reading inside and outside the root |
| `test_rejects_binary_and_large_files` | Extension guard and size-limit guard |
| `test_lists_only_selected_folder` | `list_files()` returns folder contents |
| `test_allows_relative_paths_inside_allowed_root` | Relative path resolution within a root |
| `test_rejects_relative_paths_outside_allowed_root` | `..` traversal is blocked |

## Related notes

- [[module-map]] — `tools.py` location
- [[agent-and-inference]] — how the agent detects file intents and calls FolderTools
- [[configuration-reference]] — `allowed_folders`, `file_access_enabled`, `max_file_mb`
- [[security-and-privacy]] — security model for file access
- [[architecture]] — trust boundaries and future tool-call contract