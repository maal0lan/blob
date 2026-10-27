# UI System — Crystal Companion

## Overview

The UI is built with PySide6. All windows are frameless and translucent where appropriate. The app uses `QApplication.setQuitOnLastWindowClosed(False)` so the orb and tray stay alive when the chat window is closed.

## Main windows

### OrbWindow (`crystal_agent/ui/windows.py`)

A floating, frameless, always-on-top transparent orb. Click to open chat; right-click to open settings; drag to reposition. Also supports **hold-to-speak** voice input.

- **Live refraction:** Grabs desktop pixels under the orb each frame (~30 FPS) and warps them through a lens (`LensRenderer` from `lens.py`). The orb window is excluded from screen capture via `SetWindowDisplayAffinity` (Windows 10 2004+) to avoid photographing itself.
- **Fallback:** If refraction is unavailable, paints a procedural glass orb using layered Qt gradients, animated rings, highlights, and a state-indicator ring.
- **States:** `idle`, `thinking`, `speaking`, `listening`, `error` — each changes the rim glow color. `listening` is shown while holding the orb for voice input.
- **Settings-driven:** `orb_size`, `orb_opacity`, `orb_refraction`, `orb_wobble`.
- **Hold-to-speak:** Short press (< 400ms) opens chat; long press (≥ 400ms) activates background STT via `speech_recognition.listen_in_background`. Recording stops on orb release; recognized text is sent as a user query.

### SubtitleWindow (`crystal_agent/ui/windows.py`)

A frameless glass subtitle widget positioned below the orb.

- Displays fade-in/fade-out animated text for spoken input and assistant responses
- `QGraphicsOpacityEffect` + `QPropertyAnimation` (350ms, InOutQuad) for fade in/out
- `show_text(text, hold_ms=4000)`: shows text at full opacity, fades out after hold_ms
- `bind_orb(orb)`: stores orb reference for positioning below it
- Positioned below the orb; falls back to lower-right screen area if no orb bound

### ChatWindow (`crystal_agent/ui/windows.py`)

A frameless translucent panel positioned under the orb.

- Transcript area with color-coded speakers (`YOU` = cyan, `CRYSTAL` = green, `ERROR` = pink)
- Single-line text input; Enter sends
- Buttons: Send, Settings, Diagnostics, Clear view, Close
- Supports both typed input and voice input (from hold-to-speak STT)
- Responses are not streamed; full answer appears after inference finishes

### SettingsWindow (`crystal_agent/ui/windows.py`)

Tabbed dialog with three tabs:

1. **Models & Voice:** Ollama endpoint, fast/reasoning model names, temperature, max tokens, TTS enable/model/speed/device
2. **Folder Access:** master switch + allowed folder list, add/remove folders
3. **Appearance & Privacy:** orb size/opacity, history persistence, Windows startup, diagnostics panel, error speech, max file size, max context chars, log level

Settings are saved atomically to `%APPDATA%\CrystalCompanion\settings.json`. Includes a "Test Ollama" button.

### DebugWindow (`crystal_agent/ui/windows.py`)

Live diagnostics window showing the tail of `crystal.log`, refreshed every 1.2 seconds. Can be opened from the tray menu or chat. Has a button to open the log folder.

### Tray (`CompanionApp`, `windows.py`)

System tray icon with menu: Open chat, Settings, Diagnostics, Quit Crystal.

## Glass / liquid rendering

### lens.py — `LensRenderer`

Pure numpy (with optional OpenCV acceleration) renderer that takes a BGR screenshot of the desktop behind the orb and returns a premultiplied BGRA image of a wobbly glass blob.

Features:
- Wobbly blob outline (radius varies with angle and time)
- Refraction: source pixel = centre + direction × f(radius), f grows near rim
- Chromatic dispersion: B, G, R channels sampled with slightly different offsets
- Glass body: luminance lift + saturation
- Bevel: darker band inside rim, bright rim outside
- Specular highlight + glint
- State glow on the rim (idle faint, others stronger + pulsing)

Also provides `exclude_from_capture(hwnd)` — Windows API call to hide a window from screen capture.

### glass.py — static glass chrome

For chat window and dialogs (non-animated):

- `GlassPanel` — paints a pre-rendered glass image; falls back to a flat dark rounded rect
- `GlassBackdrop` — keeps a `GlassPanel`'s glass image in sync with the desktop behind its window; samples on move/resize/visibility change
- `GlassPanelRenderer` — rounded-rect liquid glass: sharp refracting/dispersing bezel, frosted tinted interior, static rim light + soft sheen
- `DragLabel` — draggable title bar for frameless windows
- `GlassDialog` — frameless glass dialog base class with draggable title bar and close button; subclasses add widgets to `self.body_layout`

## Styling

A shared `STYLE` string in `windows.py` provides the dark translucent look: `#e7efff` text on `rgba(12,17,34,238)` backgrounds, blue accent borders, rounded corners.

## Worker pattern

`Worker` (QRunnable) + `WorkerSignals` (Qt signals) keep network/model/TTS work off the UI thread. Results and errors are emitted back via signals and connected to UI callbacks.

## Related notes

- [[project-overview]] — high-level summary
- [[architecture]] — threading model (UI thread vs workers)
- [[module-map]] — module locations
- [[agent-and-inference]] — how the chat sends queries to Ollama
- [[tts-system]] — how responses are spoken
- [[security-and-privacy]] — orb capture privacy considerations