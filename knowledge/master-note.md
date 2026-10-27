# Master Note — Crystal Companion

This is the index of all project knowledge notes. Each note links to related notes using Obsidian-style `[[wiki links]]`.

## Core notes

- [[project-overview]] — What Crystal Companion is, version, status, core facts
- [[architecture]] — System architecture, threading, state, trust boundaries, refraction options
- [[module-map]] — Every module, its responsibility, and the request lifecycle
- [[ui-system]] — Orb, chat, settings, tray, diagnostics, glass/liquid rendering
- [[agent-and-inference]] — Ollama agent, SYSTEM_PROMPT, model selection, inference controls
- [[tools-and-permissions]] — FolderTools, path safety, file intents, security model
- [[tts-system]] — Phonon TTS, licensing, synthesis flow, controls
- [[history-and-persistence]] — settings.json, SQLite history, rotating logs
- [[configuration-reference]] — All settings, defaults, validation, settings flow
- [[setup-and-deployment]] — setup.ps1, run.ps1, requirements, first launch
- [[security-and-privacy]] — Security checklist, trust boundaries, TTS licensing, limitations
- [[roadmap-and-future-work]] — Roadmap items, known limitations, future enhancements
- [[development-guide]] — Running tests, worker pattern, settings changes, adding file tools

## Quick navigation by topic

### Getting started
[[project-overview]] → [[setup-and-deployment]] → [[configuration-reference]]

### Understanding the code
[[module-map]] → [[architecture]] → [[ui-system]]

### AI / inference
[[agent-and-inference]] → [[tools-and-permissions]] → [[tts-system]]

### Data / persistence
[[history-and-persistence]] → [[configuration-reference]]

### Security
[[security-and-privacy]] → [[tools-and-permissions]]

### UI
[[ui-system]] → [[architecture]] (threading)

### Future work
[[roadmap-and-future-work]] → [[development-guide]]

### GitHub issues (local descriptions)
See `knowledge/issues/` for ready-to-create issue descriptions:
- [[issues/security-symlink-race-protection]] — reparse-point/symlink handling
- [[issues/security-secret-file-detection]] — secret-file detection and warnings
- [[issues/security-non-loopback-confirmation]] — non-loopback Ollama confirmation
- [[issues/security-delete-history-ui]] — data retention / delete-history UI
- [[issues/security-model-license-verification]] — model download/license verification
- [[issues/security-automated-tests]] — automated security tests
- [[issues/ui-60fps-glass-morphism]] — 60fps glass morphism animations
- [[issues/ui-refined-upgrades]] — refined UI upgrades
- [[issues/feature-enhanced-file-access]] — enhanced file access support
- [[issues/feature-file-modification-skills]] — file modification skills upgrades

## Project facts at a glance

| Field | Value |
|---|---|
| Name | Crystal Companion |
| Package | `crystal-companion` |
| Version | 0.2.0 |
| Status | Development prototype |
| Primary OS | Windows 10 / 11 |
| Python | >=3.11 |
| UI framework | PySide6 |
| LLM backend | Ollama (local `/api/generate`) |
| TTS | Phonon (`gradium/phonon-40m-en`) via Hugging Face |
| History | SQLite (`history.sqlite3`) |
| Settings | JSON (`settings.json`) |
| Entry point | `python -m crystal_agent` |
| Git branch | `main` |