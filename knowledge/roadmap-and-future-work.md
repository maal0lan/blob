# Roadmap and Future Work — Crystal Companion

## Suggested development order

From the README roadmap:

1. Replace the procedural orb with a real GPU-based refraction shader or safe background capture pipeline; profile GPU/CPU cost
2. Add cancellation, streamed tokens, and a proper visible task state machine
3. Add local STT (e.g. faster-whisper or Vosk), push-to-talk, and voice activity detection
4. Implement an explicit tool-call schema and confirmation prompts for every action beyond read-only file access
5. Build a tested model router that chooses the small model for simple tasks and the larger model for complex ones
6. Add full-text folder search and optional local RAG with a clear per-folder index/reset UI
7. Add per-setting validation, reset-to-defaults, import/export settings, and a model manager
8. Add multi-monitor placement, remembered orb position, keyboard shortcut, and accessibility controls
9. Add test coverage for UI, Ollama integration, TTS, startup registration, and permission boundaries
10. Package with PyInstaller, create an installer/uninstaller, and sign release builds

## Known limitations

1. **Refraction is a visual approximation** — Qt transparency shows the desktop through the orb, but no live pixel displacement yet
2. **Speech input (hold-to-speak)** — implemented via `speech_recognition.listen_in_background` (Google Web Speech API by default); local STT (faster-whisper/Vosk) is a future improvement — see [[issues/feature-hold-to-speak-subtitles]]
3. **Responses are not streamed** — full answer appears after inference finishes
4. **No automatic model router** — manual fast/reasoning selection only
5. **MCP is not connected** — the attached MCP prototype is intentionally not launched
6. **Limited file intents** — no full-text search, embeddings, RAG, file watcher, or unrestricted action system
7. **Phonon is a large dependency** — first model load can be slow and memory-heavy; license is non-commercial
8. **No packaging yet** — source-run Python app, not an installer
9. **Display/multi-monitor testing is limited** — orb appears near lower-right of primary display; position not persisted
10. **Settings fields in development** — some fields saved for future functionality without full runtime behavior

## Model router extension (from ARCHITECTURE.md)

A future router can classify task complexity with rules first, optionally use a small model as classifier, then select the fast or reasoning model. It should record the routing decision in diagnostics, offer a user override, and fall back to the fast model if the reasoning model is unavailable. Avoid calling the larger model twice for every query.

## Future tool-call contract

Do not parse arbitrary model-generated Python or shell commands. Define a strict JSON schema with a small enum of tool names and validated arguments. Check against a user-configured allowlist, show confirmation for consequential actions, execute with timeouts, cap output, and return structured success/error results.

## Refraction implementation options

1. Native composition/backdrop effects — may blur/tint a whole window; no spherical displacement map
2. Desktop capture + distortion shader — capture screen under orb, exclude app window, warp pixels with GPU shader; needs care for feedback loops, flicker, protected content, multi-monitor
3. DWM/DirectComposition custom surface — more control but requires native Windows integration

## Related notes

- [[architecture]] — refraction options, model router, tool-call contract
- [[ui-system]] — current orb rendering (lens.py procedural + painted fallback)
- [[agent-and-inference]] — current model selection (manual fast/reasoning)
- [[tools-and-permissions]] — current file tool limitations
- [[security-and-privacy]] — pending security items