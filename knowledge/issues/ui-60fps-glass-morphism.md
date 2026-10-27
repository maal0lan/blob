# Issue: 60fps glass morphism animations

## Type
ui / animation / performance

## Summary
Upgrade the glass/orb rendering to run at 60 FPS with smooth glass morphism animations.

## Current state
The orb renders at ~30 FPS (33 ms timer in `OrbWindow._tick`). The painted-glass fallback and live refraction lens (`crystal_agent/ui/lens.py`) use static/animated highlights but no true 60 FPS glass morphism. Glass panels (`crystal_agent/ui/glass.py`) sample the desktop background on move/resize only.

## Desired outcome
- Orb/lens rendering at 60 FPS (16 ms target frame budget)
- Smooth morphing/wobble animation for the glass orb
- Fluid transitions between orb states (idle/thinking/speaking/error)
- Optional GPU shader path for true desktop-pixel refraction
- Maintain the non-shader painted fallback for lower-end hardware

## Related files
- `crystal_agent/ui/lens.py` — `LensRenderer.render`, `LensRenderer.configure`
- `crystal_agent/ui/glass.py` — `GlassPanelRenderer`, `GlassBackdrop`
- `crystal_agent/ui/windows.py` — `OrbWindow._tick`, `OrbWindow._render_lens`
- `ARCHITECTURE.md` — refraction implementation options
