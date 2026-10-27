# Issue: Stronger Windows reparse-point/symlink handling and race-resistant file opens

## Type
security / permissions

## Source
SECURITY.md checklist item: **"Stronger Windows reparse-point/symlink handling and race-resistant file opens"** (currently unchecked)

## Summary
Implement stronger path canonicalization in `FolderTools` (`crystal_agent/tools.py`) to defend against Windows reparse points, symlinks, junctions, and race-condition (TOCTOU) file opens.

## Current state
`FolderTools` canonicalizes paths with `expanduser()` + `resolve()` and checks that candidates are descendants of allowed roots, but it does not specifically:
- Detect or reject symlinks / junctions / reparse points that escape allowed roots
- Use race-resistant file opening between the permission check and the actual file read

## Desired outcome
- Detect and reject symlinks/junctions/reparse points that resolve outside allowed roots
- Use race-resistant file opening where possible on Windows
- Add unit tests for symlink/junction traversal attempts
- Update SECURITY.md checklist to mark this item complete

## Related files
- `crystal_agent/tools.py` — `FolderTools._safe`, `_is_within_root`
- `tests/test_tools.py` — existing allowlist tests
- `SECURITY.md` — security checklist
