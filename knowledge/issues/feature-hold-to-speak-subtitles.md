# Issue: Hold-to-speak voice input with animated subtitles below orb

## Type
feature / ui / voice

## Status
✅ **Implemented** — see `crystal_agent/ui/windows.py` (commit `b5ab7aa` on `feature/issue-11-hold-to-speak-subtitles`)

## Summary
Enhance the orb interaction and inference UI:
- **Click** the blob to open chat (existing behavior)
- **Hold down** the blob to activate voice input / speak (STT — speech-to-text)
- **Below the blob**, show subtitles with fade in / fade out animated text outputs
- **Parse LLM responses** and display them in both the subtitle area and the chat transcript
- **Store** all exchanges in the local SQLite history (existing behavior)

## Current state (implemented)
- Orb: short click (< 400ms) opens chat; long press (≥ 400ms) activates voice input
- Hold/long-press detection on the orb via `QTimer` (400ms threshold) + `_is_holding` flag
- `SubtitleWindow`: frameless translucent widget below the orb with `QPropertyAnimation` opacity fade in/out
- `listening` orb state (glow) while holding
- STT via `speech_recognition.listen_in_background` callback pattern — records while holding, stops on release
- Recognized text sent as a user query through `CompanionApp._handle_voice_query`
- Subtitle shows both user's spoken input and Crystal's spoken responses
- Chat transcript updated; history persisted to SQLite via `history.add()`
- TTS speaks responses (existing behavior)

## Implementation details
**`OrbWindow`** (`crystal_agent/ui/windows.py`):
- `_press_time`, `_hold_threshold_ms = 400`, `_hold_timer` (single-shot QTimer), `_is_holding` flag
- `mousePressEvent`: starts hold timer, records press time
- `mouseReleaseEvent`: short click → `open_chat()`; release after hold → `_stop_voice_input()`
- `_on_hold()`: sets state to `"listening"`, calls `_start_voice_input()`
- `_start_voice_input()`: shows "Listening…" subtitle, starts a `Worker` that runs `listen_in_background` with a callback; polls `_is_holding` every 50ms (max 30s); on release, stops background listening and returns recognized text
- `_stop_voice_input()`: resets `_is_holding = False`, state to `"idle"`
- `_on_voice_result(text)`: forwards recognized text to `ctrl._handle_voice_query(text)`
- `_on_voice_error(message)`: shows error subtitle
- `_subtitle_text(text, hold_ms)`: binds orb and calls `SubtitleWindow.show_text()`

**`CompanionApp`** (`crystal_agent/ui/windows.py`):
- `_handle_voice_query(text)`: appends "YOU" to chat, shows subtitle (1500ms), sends to Ollama via `OllamaAgent.ask()`
- `_on_voice_answer(query, answer)`: appends "CRYSTAL" to chat, shows subtitle (3000ms), saves to history, triggers TTS if enabled
- `_on_voice_error_answer(message)`: appends "ERROR" to chat, shows error subtitle

**`SubtitleWindow`** (`crystal_agent/ui/windows.py`):
- Frameless glass dialog, 340×90, positioned below the orb
- `QGraphicsOpacityEffect` + `QPropertyAnimation` (350ms, InOutQuad) for fade in/out
- `show_text(text, hold_ms=4000)`: shows text at full opacity, fades out after hold_ms
- `bind_orb(orb)`: stores orb reference for positioning

## Related files
- `crystal_agent/ui/windows.py` — `OrbWindow`, `ChatWindow`, `CompanionApp`, `SubtitleWindow`
- `crystal_agent/ui/lens.py` — `LensRenderer`, `exclude_from_capture`
- `crystal_agent/agent.py` — `OllamaAgent.ask` (sends to Ollama `/api/generate`)
- `crystal_agent/tts.py` — `SpeechEngine`, `play_wav`
- `crystal_agent/history.py` — `add`, `recent`
- `README.md` — known limitation #2 (No speech input) — now addressed

## Dependencies
- STT: `speech_recognition` (uses Google Web Speech API by default); may later switch to `faster-whisper` or `Vosk` for local STT
- Subtitle animation: `QPropertyAnimation` for opacity fade in/out
