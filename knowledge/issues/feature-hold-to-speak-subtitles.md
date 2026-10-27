# Issue: Hold-to-speak voice input with animated subtitles below orb

## Type
feature / ui / voice

## Summary
Enhance the orb interaction and inference UI:
- **Click** the blob to open chat (existing behavior)
- **Hold down** the blob to activate voice input / speak (STT — speech-to-text)
- **Below the blob**, show subtitles with fade in / fade out animated text outputs
- **Parse LLM responses** and display them in both the subtitle area and the chat transcript
- **Store** all exchanges in the local SQLite history (existing behavior)

## Current state
- Orb: click opens chat, right-click opens settings, drag to reposition
- No hold/long-press detection on the orb
- No subtitle widget exists
- TTS speaks responses but there's no on-screen subtitle display
- Chat transcript shows responses; history is stored in SQLite
- Microphone / STT is not implemented (per README known limitations)

## Desired outcome
- Orb press: short press (< ~400ms) → open chat; long press (≥ ~400ms) → activate voice input
- While holding: visual feedback on the orb (e.g., "listening" state glow)
- On release of hold: capture audio, run STT, treat result as a user query
- SubtitleWindow: frameless translucent widget positioned below the orb
- Subtitle text fades in when a response starts speaking, fades out when done
- Subtitle shows both user's spoken input (from STT) and Crystal's spoken responses
- LLM responses are appended to the chat transcript (existing) AND shown in subtitles
- All exchanges are persisted to `history.sqlite3` via `history.add()` (existing)

## Related files
- `crystal_agent/ui/windows.py` — `OrbWindow`, `ChatWindow`, `CompanionApp`
- `crystal_agent/ui/lens.py` — `LensRenderer`, `STATE_COLORS`
- `crystal_agent/agent.py` — `OllamaAgent.ask`
- `crystal_agent/tts.py` — `SpeechEngine`, `play_wav`
- `crystal_agent/history.py` — `add`, `recent`
- `README.md` — known limitation #2 (No speech input)

## Dependencies
- STT: may need `faster-whisper`, `Vosk`, or similar (see roadmap item 3)
- Subtitle animation: `QPropertyAnimation` for opacity fade in/out
