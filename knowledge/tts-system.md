# TTS System — Crystal Companion

## SpeechEngine (`crystal_agent/tts.py`)

Lazy Phonon text-to-speech. Model loading is **deferred until the first spoken response** so the orb appears quickly at startup.

## Default checkpoint

- **Model ID:** `gradium/phonon-40m-en`
- **Source:** Hugging Face (gated model)
- **License:** CC BY-NC 4.0 (non-commercial use) — per the project's supplied documentation
- **Not an Ollama model** — it's a separate Hugging Face checkpoint

## Licensing note

Accept the gated model's Hugging Face terms before use. Verify the current model card/license yourself. Do not use this checkpoint in a commercial product unless the license explicitly permits your intended use. If you change TTS checkpoints, the implementation may need model-specific adaptation; changing the text field alone does not make every arbitrary model compatible with `AutoModelForTextToWaveform`.

## How synthesis works

1. Lazily imports `transformers.AutoProcessor`, `AutoModelForTextToWaveform`, `huggingface_hub.hf_hub_download`, `safetensors.torch.load_file`
2. Loads the processor and model with `device_map` (`auto`, `cpu`, or `cuda:0`)
3. Downloads `default-voice.safetensors` from the checkpoint and loads `speaker_wavs[0].T` as voice latents
4. Builds a conversation with an audio prompt and the user's text
5. Runs `model.generate()` under `torch.inference_mode()`
6. Decodes audio latents to a waveform
7. Optionally resamples for speed (0.5–2.0; changes duration, may change pitch/quality)
8. Encodes as a 24 kHz mono 16-bit WAV in memory
9. `play_wav()` plays it via `sounddevice`

## TTS controls

| Setting | Default | Range / Options |
|---|---|---|
| `tts_enabled` | `true` | Speak every assistant response |
| `tts_model` | `gradium/phonon-40m-en` | Hugging Face checkpoint ID |
| `tts_speed` | `1.0` | 0.5 – 2.0 |
| `tts_device` | `auto` | `auto`, `cpu`, `cuda:0` |
| `tts_backend` | `phonon` | Stored for future extension |

## Error behavior

- TTS errors **do not erase** the generated text response
- The chat window displays a "TTS ERROR" message
- The log records a full traceback
- `speak_errors` setting is reserved for future spoken error handling

## Dependencies

- `transformers` (pinned to a specific git revision with `AutoModelForTextToWaveform` support)
- `torch>=2.4.0`
- `accelerate>=1.0.0`
- `huggingface_hub>=0.25.0`
- `safetensors>=0.4.0`
- `sounddevice>=0.4.6`
- `numpy>=1.26`

## First-load latency

The first TTS reply may take substantially longer than later replies because model weights and voice data need to be downloaded and loaded. Keep the diagnostics window open while debugging.

## Related notes

- [[module-map]] — `tts.py` location
- [[agent-and-inference]] — how responses flow to TTS after inference
- [[ui-system]] — `ChatWindow.on_answer()` triggers TTS synthesis
- [[configuration-reference]] — all TTS settings
- [[security-and-privacy]] — model download uses the network