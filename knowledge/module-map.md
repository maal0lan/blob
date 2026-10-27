# Module Map — Crystal Companion

## Repository layout

```
crystal_companion/
├── README.md                     # User-facing documentation (features, setup, roadmap, security)
├── ARCHITECTURE.md               # Architecture notes (threading, state, trust boundaries, refraction)
├── SECURITY.md                   # Security and privacy checklist
├── requirements.txt              # Python dependencies (PySide6, httpx, torch, transformers, etc.)
├── pyproject.toml                # Packaging config (setuptools, pytest paths)
├── setup.ps1                     # One-time Windows setup (venv, deps, editable install)
├── run.ps1                       # Launch script (activates venv, runs python -m crystal_agent)
├── .env.example                  # Optional startup overrides (CRYSTAL_LOG_LEVEL=DEBUG)
├── .gitignore                    # venv, __pycache__, logs, .env, models, wav files
├── crystal_agent/
│   ├── __init__.py               # Package marker; __version__ = "0.2.0"
│   ├── __main__.py               # QApplication entry point; creates CompanionApp
│   ├── config.py                 # Settings dataclass, app-data paths, JSON persistence
│   ├── logging_setup.py          # Console + rotating file logger
│   ├── history.py                # SQLite persistence for conversations
│   ├── agent.py                  # Ollama HTTP client and prompt construction
│   ├── tools.py                  # allowlisted, read-only local text-file tools (FolderTools)
│   ├── tts.py                    # lazy Phonon synthesis and local audio playback
│   └── ui/
│       ├── __init__.py           # (implicit package marker)
│       ├── windows.py            # orb, chat, settings, tray and diagnostics UI (all Qt widgets)
│       ├── lens.py               # liquid-glass lens renderer for the orb (numpy + optional OpenCV)
│       ├── glass.py              # static liquid-glass chrome for chat window and dialogs
│       └── config.py             # UI-side Settings dataclass (glass-specific fields added)
└── tests/
    └── test_tools.py             # folder allowlist, text-only extension guard, file-size guard
```

## Module responsibilities

| Module | Responsibility |
|---|---|
| `crystal_agent/__main__.py` | Process entry point: creates `QApplication`, instantiates `CompanionApp`, starts event loop |
| `crystal_agent/config.py` | `Settings` dataclass (all user-configurable values), app-data directory, atomic JSON save/load |
| `crystal_agent/logging_setup.py` | Rotating file logger (`crystal.log`) + console stream handler |
| `crystal_agent/history.py` | SQLite `history.sqlite3`: sessions/messages tables, `add()`, `recent()`, `clear()`, `initialize()` |
| `crystal_agent/agent.py` | `OllamaAgent`: async httpx client to Ollama `/api/generate` and `/api/tags`, prompt construction, file-tool intent detection |
| `crystal_agent/tools.py` | `FolderTools`: path canonicalization, allowlist enforcement, read-only list/search/read for text files |
| `crystal_agent/tts.py` | `SpeechEngine`: lazy Phonon TTS (`AutoModelForTextToWaveform`), WAV encoding, `play_wav()` via sounddevice |
| `crystal_agent/ui/windows.py` | `OrbWindow`, `ChatWindow`, `SettingsWindow`, `DebugWindow`, `CompanionApp` controller, `Worker`/`QRunnable` |
| `crystal_agent/ui/lens.py` | `LensRenderer`: live desktop refraction (wobbly glass blob, chromatic dispersion), `exclude_from_capture()` |
| `crystal_agent/ui/glass.py` | `GlassPanel`, `GlassBackdrop`, `GlassPanelRenderer`, `DragLabel`, `GlassDialog` for static glass UI |
| `crystal_agent/ui/config.py` | UI-side `Settings` (adds `orb_refraction`, `orb_wobble`, `glass_panels`) |

## Request lifecycle

1. User clicks the orb → chat window opens
2. User types a query, presses Enter → `QRunnable` worker started
3. If file access enabled, app checks for narrow explicit file intent (list/search/read quoted path)
4. `OllamaAgent.ask()` sends conversation context + optional file result to Ollama `/api/generate`
5. Response shown in chat; if history enabled, saved in SQLite
6. If TTS enabled, Phonon loads lazily, generates WAV, `sounddevice` plays it
7. Exceptions surfaced in chat UI and logged to `crystal.log`

## Related notes

- [[architecture]] — threading, state, trust boundaries
- [[project-overview]] — high-level summary
- [[ui-system]] — UI components detail
- [[agent-and-inference]] — Ollama agent detail
- [[tools-and-permissions]] — FolderTools detail
- [[tts-system]] — Phonon TTS detail
- [[history-and-persistence]] — SQLite and JSON settings detail