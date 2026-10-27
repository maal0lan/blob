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