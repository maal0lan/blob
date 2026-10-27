# Issue: Secret-file detection and warnings

## Type
security / privacy

## Source
SECURITY.md checklist item: **"Secret-file detection and warnings"** (currently unchecked)

## Summary
Add detection and warnings for files likely containing secrets (private keys, passwords, browser profiles, credentials) before they are exposed to model context.

## Current state
`FolderTools` allows reading any text file under allowed roots with no content-based secret scanning. The security guidance in `README.md` warns users not to add folders containing private keys or credentials, but the app does not enforce or warn about it.

## Desired outcome
- Scan file names and contents for common secret patterns (keys, tokens, passwords, `.env`, `id_rsa`, etc.)
- Warn the user and block or require explicit confirmation before sending such content to the model
- Never log raw secret content to `crystal.log`
- Update SECURITY.md checklist to mark this item complete

## Related files
- `crystal_agent/tools.py` — `FolderTools.read_file`
- `crystal_agent/agent.py` — `OllamaAgent._maybe_use_file_tool`
- `SECURITY.md` — security checklist
- `README.md` — folder permissions guidance
