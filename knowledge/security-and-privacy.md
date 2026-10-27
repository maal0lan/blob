# Security and Privacy — Crystal Companion

## Security checklist (`SECURITY.md`)

| Item | Status |
|---|---|
| Folder access disabled by default | ✅ Done |
| Canonicalized path must be inside a configured folder | ✅ Done |
| Text extension allowlist; binary types rejected | ✅ Done |
| File size limit | ✅ Done |
| Read-only file operations | ✅ Done |
| No shell execution or LLM-generated code execution | ✅ Done |
| Local database and rotating logs | ✅ Done |
| Errors are visible to the user | ✅ Done |
| Stronger Windows reparse-point/symlink handling and race-resistant file opens | ⬜ Pending |
| Secret-file detection and warnings | ⬜ Pending |
| Explicit confirmation before sending file content to a non-loopback Ollama host | ⬜ Pending |
| Data retention / delete-history UI | ⬜ Pending |
| Model download/license verification workflow | ⬜ Pending |
| Automated security tests for junctions, symlinks, path traversal and concurrent file changes | ⬜ Pending |

> The current path checks are a practical guardrail, not a hardened security boundary. Run the application under a normal user account, not as Administrator. Do not grant access to folders you do not want included in prompts.

## Trust boundaries

- LLM requests go to the configured Ollama endpoint. Default local endpoint = inference is local to the machine. Model downloads and gated TTS downloads use the network.
- If the Ollama endpoint is remote, prompt and history data leave the local machine.
- Chat history is stored locally in SQLite unless disabled. Turning off future persistence does **not** delete previous history.
- Folder access is opt-in, restricted to selected roots, read-only, extension-filtered, and size-limited. It is **not** a security sandbox against every filesystem edge case.
- Never add folders containing private keys, passwords, browser profiles, credentials, or sensitive personal records.
- The agent has no shell tool, no code execution tool, and no file write/delete tool.
- MCP config is not executed by the current app. Do not enable untrusted MCP servers without reviewing their commands and permissions.
- Logs can include exception details and model/operation metadata. Avoid sharing raw logs without checking them for private paths and user content.
- The optional Windows startup feature writes a current-user Run entry. Turn it off in Settings to remove it.

## TTS licensing

The default Phonon checkpoint (`gradium/phonon-40m-en`) is identified as gated and licensed CC BY-NC 4.0 (non-commercial). Accept Hugging Face terms before use and verify the current model card/license yourself. Do not use in a commercial product unless the license explicitly permits your intended use.

## Current limitations (security-relevant)

- Path checks are a guardrail, not a hardened boundary
- No symlink/junction reparse-point handling yet
- No secret-file detection
- No confirmation before sending data to non-loopback Ollama hosts
- No data retention/delete-history UI
- MCP client has protocol and process-management risks; intentionally not launched

## Related notes

- [[architecture]] — trust boundaries section
- [[tools-and-permissions]] — FolderTools path safety and file access model
- [[tts-system]] — Phonon licensing note
- [[history-and-persistence]] — where data is stored
- [[setup-and-deployment]] — deployment recommendations