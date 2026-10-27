# Issue: Refined UI upgrades

## Type
ui / ux / polish

## Summary
Refine and polish the overall UI: smoother glass panels, better transitions, improved settings dialogs, and visual consistency across orb/chat/settings/diagnostics windows.

## Current state
UI uses PySide6 frameless translucent windows with a shared `STYLE` sheet in `crystal_agent/ui/windows.py`. Glass panels fall back to flat dark rounded rects when capture fails. Some settings fields are stored for future extension without distinct runtime behavior (`max_context_chars`, `show_debug_panel`, `speak_errors`).

## Desired outcome
- Consistent liquid-glass theme across all windows and dialogs
- Smooth show/hide transitions and state animations
- Polished Settings tabs with inline validation
- Remembered orb position and multi-monitor placement
- Keyboard shortcuts and accessibility improvements
- Better visual feedback for busy/error/speaking states

## Related files
- `crystal_agent/ui/windows.py` — all UI widgets, `STYLE`
- `crystal_agent/ui/glass.py` — glass panel rendering
- `crystal_agent/ui/lens.py` — orb lens rendering
- `crystal_agent/config.py` — settings schema
- `README.md` — known limitations (items 8, 9, 10)
