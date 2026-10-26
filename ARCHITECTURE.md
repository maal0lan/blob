# Architecture notes

## Why PySide6

PySide6 provides native windows, frameless flags, transparent window surfaces, desktop tray integration, ordinary settings dialogs and Qt painting without embedding a browser. The orb and chat are separate top-level windows so the chat can appear below the sphere while the sphere remains independently draggable.

## Threading

Qt widgets must only be updated from the UI thread. Network inference, TTS model generation and audio playback run inside `QRunnable` workers. Worker results return through Qt signals. A long-running worker should always have a bounded timeout or a cancellation design before being used in production.

## State

- Persistent preferences: JSON in the app-data directory.
- Conversation: SQLite in the app-data directory.
- Diagnostics: Python rotating file logger plus stderr/console output.
- Runtime model state: Ollama model tags and lazy-loaded Phonon model in memory.

## Trust boundaries

The Ollama endpoint receives prompts and recent history. If the endpoint is remote, that data leaves the local machine. File context is only added when folder access is enabled and the query matches a small explicit intent. `FolderTools` canonicalizes paths and checks they are descendants of allowed roots, limits supported suffixes, and rejects oversized files. Model output is displayed and spoken, never executed.

## Refraction implementation options

1. **Native composition/backdrop effects:** may blur/tint a whole window, depending on Windows version and API. It does not automatically create a spherical displacement map.
2. **Desktop capture + distortion shader:** capture the screen area under the orb, exclude/hide the app window during capture, warp pixels with a GPU shader and composite the sphere. Needs care to avoid feedback loops, flicker, protected-content limitations and multi-monitor coordinate issues.
3. **DWM/DirectComposition custom surface:** more control but requires native Windows integration and additional debugging.

A polished release should choose one route deliberately, benchmark the target hardware, and preserve a non-shader fallback.

## Model router extension

Current behavior selects one model globally using `use_reasoning_model`. A future router can classify task complexity with rules first, optionally use a small model as classifier, then select the fast or reasoning model. It should record the routing decision in diagnostics, offer a user override, and fall back to the fast model if the reasoning model is unavailable. Avoid calling the larger model twice for every query.

## Future tool-call contract

Do not parse arbitrary model-generated Python or shell commands. Define a strict JSON schema with a small enum of tool names and validated arguments. Check the tool against a user-configured allowlist, show confirmation for consequential actions, execute with timeouts, cap output, and return structured success/error results. The current code intentionally does not use the uploaded MCP client.
