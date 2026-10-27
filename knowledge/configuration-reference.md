# Configuration Reference — Crystal Companion

## All settings

Settings are stored in `%APPDATA%\CrystalCompanion\settings.json`. Defaults are defined in `crystal_agent/config.py` (core) and `crystal_agent/ui/config.py` (UI extensions).

| Setting | Default | Type | Purpose |
|---|---|---|---|
| `ollama_host` | `http://127.0.0.1:11434` | str | Local Ollama API endpoint |
| `fast_model` | `lfm2.5:350m` | str | Fast model tag for everyday requests |
| `reasoning_model` | `phi2` | str | Mid-tier/reasoning model tag |
| `use_reasoning_model` | `false` | bool | Selects which model handles requests |
| `tts_enabled` | `true` | bool | Speak every assistant response |
| `tts_backend` | `phonon` | str | TTS backend (future extension) |
| `tts_model` | `gradium/phonon-40m-en` | str | Hugging Face TTS checkpoint |
| `tts_speed` | `1.0` | float | Speech speed (0.5–2.0) |
| `tts_device` | `auto` | str | TTS device map (`auto`, `cpu`, `cuda:0`) |
| `allowed_folders` | `[]` | list[str] | Explicit directory allowlist |
| `file_access_enabled` | `false` | bool | Master switch for file tools |
| `max_file_mb` | `2` | int | Maximum readable file size (MB) |
| `max_context_chars` | `14000` | int | Cap on file context for prompt (guardrail) |
| `temperature` | `0.55` | float | Generation randomness |
| `max_tokens` | `600` | int | Maximum output tokens |
| `orb_size` | `180` | int | Orb diameter in pixels |
| `orb_opacity` | `0.98` | float | Orb paint opacity |
| `orb_refraction` | `true` | bool | Live glass refraction on the orb (UI config) |
| `orb_wobble` | `1.0` | float | 0 = circle, 1 = gentle blob (UI config) |
| `glass_panels` | `true` | bool | Glass look for chat window + dialogs (UI config) |
| `start_with_windows` | `false` | bool | Register current-user Windows Run entry |
| `show_debug_panel` | `true` | bool | UI preference for diagnostics |
| `speak_errors` | `false` | bool | Reserved for future spoken error handling |
| `remember_history` | `true` | bool | Persist messages in local SQLite |
| `log_level` | `DEBUG` | str | Logging verbosity |

## Notes on settings

- **`max_context_chars`** — guardrail for future larger context assembly; not yet used to trim file context at the agent level (the agent caps file context at this value when building the prompt)
- **`show_debug_panel`** — preference flag; the diagnostics panel can also be opened from the tray regardless
- **`speak_errors`** — reserved; not yet wired to behavior
- **`orb_refraction`, `orb_wobble`, `glass_panels`** — defined in `crystal_agent/ui/config.py` (UI-side Settings); not present in the core `crystal_agent/config.py`

## Settings flow

1. User edits values in `SettingsWindow` (three tabs: Models & Voice, Folder Access, Appearance & Privacy)
2. Clicking "Save settings" calls `collect()` → validates → `s.save()` → emits `saved` signal
3. `CompanionApp.apply_settings()` updates the live `settings` object, agent, orb, and log level
4. `set_windows_startup()` registers/unregisters the Windows Run registry entry

## Validation

- Ollama endpoint and both model names are required (non-empty)
- Model availability is verified at request time; use "Test Ollama" for a connection check
- Folder paths must exist and be directories to be added to the allowlist

## Related notes

- [[module-map]] — `config.py` and `ui/config.py` locations
- [[history-and-persistence]] — where settings.json lives, atomic write behavior
- [[agent-and-inference]] — how settings drive model selection and inference
- [[tools-and-permissions]] — how `allowed_folders` and `max_file_mb` drive file access
- [[ui-system]] — how settings drive orb appearance and glass panels