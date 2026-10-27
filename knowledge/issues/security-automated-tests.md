# Issue: Automated security tests for junctions, symlinks, path traversal and concurrent file changes

## Type
security / testing

## Source
SECURITY.md checklist item: **"Automated security tests for junctions, symlinks, path traversal and concurrent file changes"** (currently unchecked)

## Summary
Add automated tests covering filesystem security boundaries: junctions, symlinks, path traversal, and concurrent file changes.

## Current state
`tests/test_tools.py` covers allowlist enforcement, extension guard, size guard, listing, and relative-path traversal, but does not test symlinks, junctions, or concurrency.

## Desired outcome
- Tests for symlink and junction escape attempts (Windows reparse points)
- Tests for path traversal (`..`, absolute paths outside roots)
- Tests for concurrent file changes during read (race conditions / TOCTOU)
- Tests run on Windows where reparse points apply
- Update SECURITY.md checklist to mark this item complete

## Related files
- `tests/test_tools.py` — existing FolderTools tests
- `crystal_agent/tools.py` — `FolderTools` path safety
- `SECURITY.md` — security checklist
