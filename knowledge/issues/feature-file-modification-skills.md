# Issue: File modification skills upgrades

## Type
feature / tools / security

## Source
`ARCHITECTURE.md` — "Future tool-call contract" section

## Summary
Add file modification capabilities (write, edit, delete, create) behind a strict tool-call schema with user confirmation, allowlisting, timeouts, and structured results.

## Current state
The app is deliberately read-only: no file writes, deletes, shell commands, or program execution. The MCP prototype is intentionally not wired into the app. `FolderTools` only supports list/search/read.

Per `ARCHITECTURE.md`, the future tool-call contract requires:
- A strict JSON schema with a small enum of tool names and validated arguments
- Checking the tool against a user-configured allowlist
- Showing confirmation for consequential actions
- Executing with timeouts and capping output
- Returning structured success/error results
- Not parsing arbitrary model-generated Python or shell commands

## Desired outcome
- Strict JSON tool schema (enum: `write_file`, `edit_file`, `delete_file`, `create_file`, etc.)
- Validated arguments for each tool
- User-configured allowlist for which modifications are permitted
- Explicit confirmation dialog before any write/delete action
- Execution timeouts and output caps
- Structured success/error results returned to the model and UI
- Audit logging of all file modifications

## Related files
- `crystal_agent/tools.py` — `FolderTools` (read-only currently)
- `crystal_agent/agent.py` — `OllamaAgent` tool intent detection
- `crystal_agent/ui/windows.py` — confirmation dialogs
- `ARCHITECTURE.md` — future tool-call contract
- `SECURITY.md` — no shell execution / no code execution checklist items
