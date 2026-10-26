# Security and privacy checklist

- [x] Folder access disabled by default.
- [x] Canonicalized path must be inside a configured folder.
- [x] Text extension allowlist; binary types rejected.
- [x] File size limit.
- [x] Read-only file operations.
- [x] No shell execution or LLM-generated code execution.
- [x] Local database and rotating logs.
- [x] Errors are visible to the user.
- [ ] Stronger Windows reparse-point/symlink handling and race-resistant file opens.
- [ ] Secret-file detection and warnings.
- [ ] Explicit confirmation before sending file content to a non-loopback Ollama host.
- [ ] Data retention / delete-history UI.
- [ ] Model download/license verification workflow.
- [ ] Automated security tests for junctions, symlinks, path traversal and concurrent file changes.

The current path checks are a practical guardrail, not a hardened security boundary. Run the application under a normal user account, not as Administrator. Do not grant access to folders you do not want included in prompts.
