# Issue: Model download/license verification workflow

## Type
security / licensing

## Source
SECURITY.md checklist item: **"Model download/license verification workflow"** (currently unchecked)

## Summary
Add a workflow to verify model downloads and licenses, especially the gated Phonon TTS checkpoint (CC BY-NC 4.0 non-commercial).

## Current state
The default TTS checkpoint `gradium/phonon-40m-en` is identified as gated and CC BY-NC 4.0 (non-commercial). Users accept Hugging Face terms manually outside the app; there is no app-level license check or verification. Ollama model tags are also not verified for licensing.

## Desired outcome
- Surface license information for downloaded models (Ollama tags and HF checkpoints)
- Warn if a model's license is non-commercial and usage may be commercial
- Option to verify/acknowledge model licenses in Settings
- Log model downloads and license acknowledgments
- Update SECURITY.md checklist to mark this item complete

## Related files
- `crystal_agent/tts.py` — `SpeechEngine._load`, model download
- `crystal_agent/config.py` — `Settings.tts_model`, `Settings.fast_model`, `Settings.reasoning_model`
- `crystal_agent/ui/windows.py` — `SettingsWindow` Models & Voice tab
- `SECURITY.md` — security checklist
- `README.md` — Phonon TTS licensing note
