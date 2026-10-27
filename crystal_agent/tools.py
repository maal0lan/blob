"""Conservative local-file tools. No shell, execution, or arbitrary filesystem access."""
from pathlib import Path

TEXT_SUFFIXES = {".txt", ".md", ".py", ".json", ".csv", ".log", ".yaml", ".yml", ".toml", ".ini", ".html", ".css", ".js", ".ts", ".sql", ".xml"}

class FolderTools:
    def __init__(self, folders: list[str], max_file_mb: int = 2):
        self.roots = []
        for raw in folders:
            p = Path(raw).expanduser()
            if p.exists() and p.is_dir():
                self.roots.append(p.resolve())
        self.max_bytes = max_file_mb * 1024 * 1024

    def _is_within_root(self, candidate: Path) -> bool:
        resolved = candidate.resolve(strict=False)
        return any(resolved == root or root in resolved.parents for root in self.roots)

    def _safe(self, raw: str) -> Path:
        if raw is None:
            raise PermissionError("That path is outside the folders you allowed in Settings.")

        candidate = Path(raw).expanduser()
        if not candidate.is_absolute():
            candidates = [(root / candidate).resolve(strict=False) for root in self.roots]
        else:
            candidates = [candidate.resolve(strict=False)]

        for p in candidates:
            if self._is_within_root(p):
                return p
        raise PermissionError("That path is outside the folders you allowed in Settings.")

    def list_files(self, folder: str = "", limit: int = 100) -> str:
        base = self._safe(folder) if folder else (self.roots[0] if self.roots else None)
        if base is None: return "No allowed folders are configured. Add one in Settings."
        if not base.is_dir(): return f"Not a directory: {base}"
        items = []
        for p in sorted(base.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))[:max(1, min(limit, 250))]:
            items.append(("[DIR] " if p.is_dir() else "[FILE] ") + p.name)
        return "\n".join(items) or "This folder is empty."

    def search_files(self, query: str, limit: int = 30) -> str:
        if not self.roots: return "No allowed folders are configured."
        q = query.casefold(); matches = []
        for root in self.roots:
            for p in root.rglob("*"):
                if len(matches) >= min(max(limit, 1), 100): break
                try:
                    if p.is_file() and q in p.name.casefold(): matches.append(str(p))
                except (OSError, PermissionError): continue
        return "\n".join(matches) or "No matching filenames found."

    def read_file(self, path: str) -> str:
        p = self._safe(path)
        if not p.is_file(): raise ValueError("The requested path is not a file.")
        if p.suffix.lower() not in TEXT_SUFFIXES: raise ValueError(f"Reading {p.suffix or 'extensionless'} files is disabled. Supported text types: {', '.join(sorted(TEXT_SUFFIXES))}")
        if p.stat().st_size > self.max_bytes: raise ValueError(f"File exceeds the configured {self.max_bytes // (1024*1024)} MB limit.")
        return p.read_text(encoding="utf-8", errors="replace")[:120_000]
