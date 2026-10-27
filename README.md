# Crystal Companion — native desktop AI orb

**Status:** development prototype / v0.2.0. This is a native Python + Qt desktop app, not a website wrapped in a browser frame. The transparent orb and chat/settings windows are separate frameless desktop windows. Ollama handles text generation locally; an optional local Hugging Face Phonon model synthesizes spoken answers.

> **Reality check:** the orb and chat/settings/diagnostics panels use native Qt windows. The orb and panels sample and refract desktop pixels when Windows capture exclusion is available; otherwise they fall back to painted glass. This is not a GPU shader. Push-to-talk speech recognition uses Google's online recognition service; typed input remains available. TTS model licensing and system compatibility must be checked before use.

## Contents

- [Features and current status](#features-and-current-status)
- [Architecture](#architecture)
- [Requirements](#requirements)
- [Windows setup](#windows-setup)
- [First launch](#first-launch)
- [Model setup and switching](#model-setup-and-switching)
- [Phonon text-to-speech](#phonon-text-to-speech)
- [Folder permissions and local tools](#folder-permissions-and-local-tools)
- [Settings reference](#settings-reference)
- [Diagnostics and logs](#diagnostics-and-logs)
- [Tests and development](#tests-and-development)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Security and privacy](#security-and-privacy)
- [Roadmap](#roadmap)

## Features and current status

| Feature | Status | Notes |
|---|---|---|
| Native desktop UI | Implemented | PySide6; not a browser wrapper |
| Transparent, frameless, always-on-top orb | Implemented | Drag to reposition; click to open chat; right-click opens settings |
| Glass orb and panels | Prototype | Live desktop sampling/refraction when supported; painted fallback otherwise |
| Bottom chat panel | Implemented | Frameless `GlassDialog`; Enter sends; response transcript |
| Background/tray operation | Implemented | Close chat to hide it; tray menu has chat/settings/diagnostics/quit |
| Separate settings window | Implemented | `GlassDialog` shell; model, TTS, folders, UI, privacy and logging controls |
| Ollama local text generation | Implemented | Uses local `/api/generate`; non-streaming request for each reply |
| Fast and reasoning model choices | Implemented | Two independent model-name settings; choose the active route in Settings |
| Spoken assistant answers | Implemented with setup | Phonon model is lazy-loaded; first synthesis can take a while |
| Persistent conversation history | Implemented | SQLite file under the app-data directory; setting can disable persistence |
| Selected-folder access | Limited implementation | Explicit list/search/read intents; only supported text files; read-only |
| Visible diagnostics | Implemented | Live log window plus rotating log file and console output |
| Launch on Windows sign-in | Implemented | Optional current-user Run registry entry; disable in Settings to remove it |
| Microphone / STT | Implemented | Hold the orb for push-to-talk; Google recognition needs internet access |
| MCP integrations | Not wired into the new desktop app | The uploaded MCP prototype is not automatically launched; see security note |
| Autonomous shell / arbitrary computer control | Deliberately absent | No shell execution or arbitrary program launching |
| Real optical desktop refraction | Not implemented | Needs a dedicated shader/capture implementation and testing |

## Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                       Desktop session                         │
│                                                              │
│  ┌─────────────┐   click    ┌──────────────────────────────┐  │
│  │ Crystal orb │ ─────────► │ Frameless chat panel         │  │
│  │ Qt painter  │            │ Enter → worker thread        │  │
│  └─────────────┘            └──────────────┬───────────────┘  │
│                                           │                  │
│  ┌─────────────┐                          ▼                  │
│  │ Settings    │                 OllamaAgent (httpx)         │
│  │ window      │                 ├─ selected model           │
│  └─────────────┘                 └─ allowlisted file tools   │
│                                           │                  │
│  ┌─────────────┐                          ▼                  │
│  │ Diagnostics│                 assistant text               │
│  └─────────────┘                          │                  │
│                                           ▼                  │
│                                  Phonon TTS → sounddevice     │
└──────────────────────────────────────────────────────────────┘
                 │                         │
                 ▼                         ▼
       %APPDATA%\CrystalCompanion\   Ollama at 127.0.0.1:11434
       settings.json / history DB / log
```

### Module map

```text
crystal_companion/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── setup.ps1
├── run.ps1
├── crystal_agent/
│   ├── __init__.py
│   ├── __main__.py       # QApplication and process entry point
│   ├── config.py         # Settings schema, app-data paths, JSON persistence
│   ├── logging_setup.py  # Console + rotating file logger
│   ├── history.py        # SQLite persistence
│   ├── agent.py          # Ollama HTTP client and prompt construction
│   ├── tools.py          # allowlisted, read-only local text-file tools
│   ├── tts.py            # lazy Phonon synthesis and local audio playback
│   └── ui/
│       ├── glass.py      # shared refractive shell for chat and dialogs
│       ├── lens.py       # orb/panel desktop sampling and glass rendering
│       └── windows.py    # orb, chat, settings, tray and diagnostics UI
└── tests/
    └── test_tools.py     # folder allowlist and file-size/type safety tests
```

### Request lifecycle

1. User clicks the orb, enters a query and presses Enter.
2. The UI starts a `QRunnable` worker. Network/model work is kept off the Qt UI thread.
3. If file access is enabled, the app checks for a narrow explicit file intent (list, filename search, or read a quoted file path). It does not execute file contents.
4. The agent sends the recent conversation context and optional file result to Ollama's local `/api/generate` endpoint.
5. The response is shown in the chat window and, if history is enabled, saved in SQLite.
6. If TTS is enabled, Phonon loads lazily if needed, generates a WAV, and `sounddevice` plays it.
7. Exceptions are surfaced in the chat UI and logged to `crystal.log`.

## Requirements

- Windows 10/11 is the primary target. Most UI features may work on other Qt platforms, but Windows startup integration is Windows-only.
- Python 3.11 or 3.12 recommended.
- Ollama installed and running locally.
- At least one Ollama model downloaded.
- Disk space for Python packages, PyTorch and the TTS model cache.
- A working speaker/audio output for TTS.
- Optional GPU: PyTorch/Transformers may use an available supported accelerator; `device_map=auto` decides placement. The default setup is not guaranteed to fit every GPU or RAM budget.

### Model names must match Ollama

Ollama model tags differ from Hugging Face model IDs. The strings in Settings must exactly match the names returned by `ollama list` / `/api/tags`. For example, `lfm2.5:350m`, `phi2`, or `mistral:7b` are configurable examples, not a guarantee that those exact tags are available on every Ollama install. If a tag does not exist, use the exact installed tag or pull the model first.

## Windows setup

Open PowerShell in the extracted project directory.

### 1. Create a virtual environment

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
```

If PowerShell blocks activation, either allow scripts for the current user (only if you understand the policy) or use the environment's Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel
```

### 2. Install Python dependencies

```powershell
python -m pip install -r requirements.txt
```

The pinned Transformers revision is required because the Phonon model uses `AutoModelForTextToWaveform`, which may not exist in a standard released Transformers build. PyTorch installation can be large and accelerator-specific; if pip chooses an unsuitable build, use the official PyTorch install selector for your CPU/CUDA setup, then install the remaining requirements.

### 3. Install and start Ollama

Install Ollama from its official distribution, then open a separate terminal and verify:

```powershell
ollama --version
ollama list
```

Pull the model tags you want. Examples:

```powershell
ollama pull lfm2.5:350m
ollama pull phi2
# Alternative larger model, if your machine has enough memory:
ollama pull mistral:7b
```

A model tag may be unavailable or named differently in your Ollama catalogue. If a `pull` fails, select a real tag from the Ollama library and put that exact tag in Settings. The application does not silently download LLMs itself.

Verify Ollama responds:

```powershell
Invoke-RestMethod http://127.0.0.1:11434/api/tags
```

### 4. Start Crystal

```powershell
python -m crystal_agent
```

Or run `setup.ps1` once and `run.ps1` for subsequent launches. The app should display a floating orb and a tray icon. It does not open a browser or start a web server.

## First launch

1. Right-click the orb to open **Settings**, or use the tray icon's Settings menu.
2. Under **Models & Voice**, set the Ollama endpoint and model names.
3. Click **Test Ollama** to verify connectivity and inspect installed model names.
4. Choose whether the fast model or reasoning model should handle requests.
5. Keep TTS enabled if you want every successful assistant response spoken aloud. Accept the Phonon checkpoint terms on Hugging Face before loading it.
6. If you want local file access, go to **Folder Access**, add only the folders the agent should inspect, and explicitly enable folder access.
7. Click **Save settings**.
8. Click the orb and ask a question. Press Enter to send. Use **Diagnostics** to see startup, model, TTS and error messages.

The first TTS reply may take substantially longer than later replies because model weights and voice data need to be downloaded and loaded. Keep the diagnostics window open while debugging.

## Model setup and switching

The app exposes two text model settings:

- **Fast model**: intended for low-latency everyday requests; a small LiquidAI/Ollama-compatible model is a reasonable candidate.
- **Reasoning / mid-tier model**: intended for more involved prompts; Phi-2 or a larger model such as Mistral 7B may be selected if installed and supported by your machine.

The `Use reasoning model for all requests` checkbox selects which model is used for each query. This version does **not** yet automatically classify a request and route only difficult questions to the larger model. The checkbox is explicit so that model selection is predictable and easy to debug.

Model names are stored in `%APPDATA%\CrystalCompanion\settings.json`. You can change them in the UI without editing Python code. Settings are validated for non-empty names, but the app verifies actual model availability when the request is sent; use **Test Ollama** for a connection check and `ollama list` to inspect models.

### Inference controls

- **Temperature**: lower values are generally more predictable; higher values permit more variation.
- **Maximum output tokens**: upper limit for the response. Large values can increase latency and memory use.
- **Ollama endpoint**: default `http://127.0.0.1:11434`. Do not point it at an untrusted remote endpoint unless you understand what data will be sent there.

The current client uses a single non-streaming `/api/generate` request. The full answer appears after inference finishes; true token-by-token streaming is a planned enhancement.

## Phonon text-to-speech

The default TTS checkpoint is `gradium/phonon-40m-en`. It is a Hugging Face model, **not an Ollama model**. The first synthesis lazily imports Transformers, loads the processor/model and fetches the checkpoint's default voice file. Audio is encoded as a temporary in-memory WAV and played locally through `sounddevice`.

### Important licensing note

The project files you supplied identify this checkpoint as gated and licensed **CC BY-NC 4.0** (non-commercial use). Accept its Hugging Face terms before use and verify the current model card/license yourself. Do not use this checkpoint in a commercial product unless the license explicitly permits your intended use. If you change TTS checkpoints, the implementation may need model-specific adaptation; changing the text field alone does not make every arbitrary model compatible with `AutoModelForTextToWaveform`.

### TTS controls

- **Speak every assistant response**: enables/disables speech generation.
- **TTS Hugging Face model**: checkpoint ID.
- **Speech speed**: 0.5–2.0. This prototype changes duration by resampling the waveform, which can change pitch/quality.
- **TTS device map**: `auto`, `cpu`, or `cuda:0`. Hardware and PyTorch build must support the selected option.

TTS errors do not erase the generated text response. The chat window displays an error and the log records a traceback. The current voice is the checkpoint's default voice; a custom voice picker is not implemented.

## Folder permissions and local tools

Folder access is **off by default**. Add exact directories under Settings → Folder Access, then enable access. The current implementation has a deliberately small read-only tool surface:

- List the top level of the first configured folder when the query clearly asks to list/show files or a folder.
- Search filenames when the query clearly asks to find/search files. This searches names, not file contents.
- Read a text file when the query contains an explicit quoted path, for example `Read the file "C:\\Users\\you\\Documents\\notes.md"`.

Supported text suffixes include `.txt`, `.md`, `.py`, `.json`, `.csv`, `.log`, `.yaml`, `.yml`, `.toml`, `.ini`, `.html`, `.css`, `.js`, `.ts`, `.sql`, and `.xml`. Binary files are rejected. Files above the configured size limit are rejected. Path resolution checks that a requested file remains inside one of the configured roots.

### Current limitations of file tools

- This is not yet a general-purpose autonomous agent loop. It recognizes a few explicit intents rather than allowing the LLM to call arbitrary tools.
- Search is filename-only; full-text indexing/RAG is not included in this desktop prototype.
- Folder selection is an access boundary, not a substitute for OS permissions. The app runs with your Windows account's permissions.
- Do not add a whole drive or your home folder unless you genuinely want to expose its text-file contents to the local model context.
- File access is read-only. No file writes, deletes, shell commands or program execution are implemented.

## Settings reference

Settings are saved atomically to `%APPDATA%\CrystalCompanion\settings.json`. On most Windows installations that resolves under your user profile's AppData/Roaming directory. The application creates its data directory automatically.

| Setting | Default | Purpose |
|---|---|---|
| `ollama_host` | `http://127.0.0.1:11434` | Local Ollama API endpoint |
| `fast_model` | `lfm2.5:350m` | Fast model tag; editable |
| `reasoning_model` | `phi2` | Mid-tier/reasoning model tag; editable |
| `use_reasoning_model` | `false` | Chooses which model receives requests |
| `temperature` | `0.55` | Generation randomness |
| `max_tokens` | `600` | Maximum generated tokens |
| `tts_enabled` | `true` | Speak assistant responses |
| `tts_model` | `gradium/phonon-40m-en` | Hugging Face TTS checkpoint |
| `tts_speed` | `1.0` | Playback-duration adjustment |
| `tts_device` | `auto` | TTS model device map |
| `allowed_folders` | `[]` | Explicit directory allowlist |
| `file_access_enabled` | `false` | Master switch for file tools |
| `max_file_mb` | `2` | Maximum readable file size |
| `max_context_chars` | `14000` | Cap on file context prepared for the prompt |
| `orb_size` | `180` | Orb diameter in pixels |
| `orb_opacity` | `0.98` | Orb paint opacity |
| `glass_panels` | `true` | Enable desktop-sampled glass for chat, settings and diagnostics |
| `remember_history` | `true` | Persist messages in local SQLite |
| `show_debug_panel` | `true` | UI preference for diagnostics (panel can also be opened from tray) |
| `speak_errors` | `false` | Reserved for future spoken error handling |
| `start_with_windows` | `false` | Register/unregister current-user Windows startup entry |
| `log_level` | `DEBUG` | Logging verbosity |

A few settings are currently stored for future extension and do not yet drive a distinct feature (`max_context_chars` is a guardrail for future larger context assembly; `show_debug_panel` is a preference flag; `speak_errors` is reserved). See the known limitations section rather than assuming every saved field has full runtime behavior.

## Diagnostics and logs

The app is deliberately noisy during development.

- **Diagnostics window**: open from chat or tray. It refreshes the log file while open.
- **Log file**: `%APPDATA%\CrystalCompanion\crystal.log`.
- **Rotation**: up to 2 MB per file and four backup files.
- **Console**: startup and errors are also written to the terminal when launched with `python -m crystal_agent`.
- **Chat errors**: request and TTS failures are displayed in the transcript so the UI does not silently swallow them.
- **History database**: `%APPDATA%\CrystalCompanion\history.sqlite3`.
- **Settings**: `%APPDATA%\CrystalCompanion\settings.json`.

Useful diagnostic sequence:

1. Launch from PowerShell, not by double-clicking a hidden Python process.
2. Open Diagnostics before sending a query.
3. Click **Test Ollama** in Settings.
4. Check that the exact selected model tag appears in `ollama list`.
5. Send a short text prompt with TTS disabled. If this works, re-enable TTS and isolate speech failures separately.
6. Inspect the last traceback in `crystal.log` and include it when reporting a bug. Redact personal paths or sensitive prompt text before sharing logs.

## Tests and development

Install dev requirements as part of `requirements.txt`, then run:

```powershell
python -m compileall -q crystal_agent tests
python -m pytest -q
```

The current tests cover the folder allowlist, text-only extension guard, file-size guard and basic listing. They do not test the Qt event loop, a real Ollama server, model downloads, audio hardware or the Windows compositor.

### Development recommendations

- Keep network/model work out of the Qt UI thread. Use worker threads and signal results back to widgets.
- Keep settings schema changes in `config.py`, then wire them into `SettingsWindow` and runtime code.
- Put all file-system access behind `FolderTools`; do not add an unrestricted `open(path)` call in UI or prompt code.
- Use `logging` rather than bare `print()` for new subsystems, and surface actionable errors in the UI.
- Avoid importing Torch/Transformers during application startup; lazy-load them so the orb can appear quickly.
- Add tests for every file permission boundary and error path.
- Treat file contents and model output as untrusted. Never directly execute text emitted by an LLM.

## Known limitations

1. **Refraction is a visual approximation.** Qt transparency shows the desktop through the orb, but the current paint code does not displace the actual pixels behind the orb. True refraction likely needs a Windows composition/capture strategy or a GPU shader and careful exclusion of the app window to avoid recursive capture.
2. **Speech recognition uses an online service.** Hold the orb to record a spoken query; the captured audio is sent to Google's recognition service for transcription. Typed input is available as an alternative.
3. **Responses are not streamed.** The agent waits for the complete Ollama response before showing it.
4. **No automatic model router.** You manually select fast or reasoning model mode.
5. **MCP is not connected.** The attached `mcp_client.py` prototype has protocol and process-management risks and is intentionally not launched by this app. Integrate it only after adding proper JSON-RPC framing, stderr/stdout separation, per-tool allowlists, timeouts, cancellation and user consent.
6. **Limited file intents.** There is no full-text search, embeddings, RAG, file watcher, or unrestricted action system.
7. **Phonon is a large dependency.** First model load can be slow and memory-heavy; its license is non-commercial according to the supplied documentation.
8. **No packaging yet.** This is a source-run Python app, not an installer or signed executable.
9. **Display / multi-monitor testing is limited.** The orb initially appears near the lower-right of the primary display; its position is not persisted yet.
10. **Settings fields in development.** Some fields are saved in preparation for future functionality and are documented above.

## Troubleshooting

### `Cannot connect to Ollama`

- Start Ollama and verify `http://127.0.0.1:11434/api/tags` responds.
- Confirm the host field has no typo and no trailing path like `/api/generate`.
- Check that another app has not changed the Ollama port.

### `model not found` / HTTP 404

- Run `ollama list` and copy the exact model tag into Settings.
- Pull the model if it is available in your Ollama catalogue.
- Do not use a Hugging Face repository ID as an Ollama tag unless your Ollama runtime explicitly supports that name.

### Voice input does not work

- Hold the orb (do not just click it) while speaking; release it to send the recognized query.
- Allow microphone access in Windows privacy settings and select a working input device.
- SpeechRecognition uses Google's online recognition service, so an internet connection is required and microphone audio is sent for transcription.
- Confirm `SpeechRecognition` and `PyAudio` are installed in the same virtual environment used to launch Crystal.

### Phonon import/model loading fails

- Confirm you installed the pinned Transformers revision from `requirements.txt` in the same virtual environment running Crystal.
- Accept the gated model terms and authenticate with Hugging Face if required.
- Check disk space, network access for the first download, PyTorch version and memory availability.
- Temporarily disable TTS to confirm text inference works independently.
- If the selected TTS checkpoint is incompatible, return to `gradium/phonon-40m-en` or implement its specific processor/model adapter.

### No audio / `sounddevice` error

- Verify Windows has an active output device and it is not muted.
- Run `python -c "import sounddevice as sd; print(sd.query_devices())"`.
- Reinstall `sounddevice` and its PortAudio dependency if the import or device query fails.
- Try a CPU TTS device if accelerator loading fails.

### App window disappears when I close chat

This is expected. The orb and tray icon stay alive because `QApplication.setQuitOnLastWindowClosed(False)` is set. Use the tray menu → Quit Crystal to exit fully.

### Orb is visible but doesn't distort wallpaper enough

This version has procedural highlights and rings, not live pixel refraction. That effect is a separate graphics task, not a settings issue.

### Folder tool says access denied

- Enable the master folder-access checkbox.
- Add the folder containing the target file, not just a sibling directory.
- Use a quoted absolute path in the explicit read-file query.
- Check extension and file size restrictions.

### Settings do not persist

- Check write access to `%APPDATA%\CrystalCompanion`.
- Inspect `crystal.log` for JSON/permission errors.
- The current code writes a temporary JSON file and replaces the old settings file after successful serialization.

## Security and privacy

- LLM requests go to the configured Ollama endpoint. With the default local endpoint, inference is local to the machine, but model downloads and gated TTS downloads use the network.
- Push-to-talk transcription uses Google's online speech recognition service; microphone audio leaves the device for transcription. Do not use voice input for sensitive content.
- Chat history is stored locally in SQLite unless disabled. Turning off future persistence does not delete previous history; remove the database only after quitting the app if you want to erase it.
- Folder access is opt-in, restricted to selected roots, read-only, extension-filtered and size-limited. It is not a security sandbox against every possible filesystem edge case.
- Never add folders containing private keys, passwords, browser profiles, credentials or sensitive personal records.
- The agent has no shell tool, no code execution tool and no file write/delete tool.
- MCP config is not executed by the current app. Do not enable untrusted MCP servers without reviewing their commands and permissions.
- Logs can include exception details and model/operation metadata. Avoid sharing raw logs without checking them for private paths and user content.
- The optional Windows startup feature writes a current-user Run entry. Turn it off in Settings to remove that entry.

## Roadmap

Suggested order for future development:

1. Replace the procedural orb with a real GPU-based refraction shader or safe background capture pipeline; profile GPU/CPU cost.
2. Add cancellation, streamed tokens and a proper visible task state machine.
3. Replace online speech recognition with local STT (e.g. faster-whisper or Vosk) and add voice activity detection.
4. Implement an explicit tool-call schema and confirmation prompts for every action beyond read-only file access.
5. Build a tested model router that chooses the small model for simple tasks and the larger model for complex ones.
6. Add full-text folder search and optional local RAG with a clear per-folder index/reset UI.
7. Add per-setting validation, reset-to-defaults, import/export settings and a model manager.
8. Add multi-monitor placement, remembered orb position, keyboard shortcut and accessibility controls.
9. Add test coverage for UI, Ollama integration, TTS, startup registration and permission boundaries.
10. Package with PyInstaller, create an installer/uninstaller and sign release builds.

---

**Development note:** the attached browser version and its backend were used as reference material, but this implementation is a clean native desktop foundation. It does not claim the original browser prototype's advertised streaming, microphone, MCP, or shader capabilities are already complete here.
