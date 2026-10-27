# Issue: Explicit confirmation before sending file content to non-loopback Ollama host

## Type
security / privacy / network

## Source
SECURITY.md checklist item: **"Explicit confirmation before sending file content to a non-loopback Ollama host"** (currently unchecked)

## Summary
Require explicit user confirmation before sending file contents to any Ollama endpoint that is not loopback (127.0.0.1/localhost).

## Current state
File contents are sent to the configured `ollama_host` with no distinction between local and remote endpoints. If a user points the endpoint at a remote host, file context could leave the machine without warning.

## Desired outcome
- Detect when `ollama_host` is not a loopback address
- Show an explicit confirmation dialog before transmitting file context to a remote host
- Log when remote-host file transmission occurs (with redacted content)
- Update SECURITY.md checklist to mark this item complete

## Related files
- `crystal_agent/config.py` — `Settings.ollama_host`
- `crystal_agent/agent.py` — `OllamaAgent.ask`, file context building
- `crystal_agent/ui/windows.py` — `SettingsWindow`, confirmation dialogs
- `SECURITY.md` — security checklist
