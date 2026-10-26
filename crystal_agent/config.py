from __future__ import annotations
import json, os
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_DIR = Path(os.getenv("APPDATA", Path.home())) / "CrystalCompanion"
CONFIG_PATH = APP_DIR / "settings.json"

@dataclass
class Settings:
    ollama_host: str = "http://127.0.0.1:11434"
    fast_model: str = "lfm2.5:350m"
    reasoning_model: str = "phi2"
    use_reasoning_model: bool = False
    tts_enabled: bool = True
    tts_backend: str = "phonon"
    tts_model: str = "gradium/phonon-40m-en"
    tts_speed: float = 1.0
    tts_device: str = "auto"
    allowed_folders: list[str] = field(default_factory=list)
    file_access_enabled: bool = False
    max_file_mb: int = 2
    max_context_chars: int = 14000
    temperature: float = 0.55
    max_tokens: int = 600
    orb_size: int = 180
    orb_opacity: float = 0.98
    start_with_windows: bool = False
    show_debug_panel: bool = True
    speak_errors: bool = False
    remember_history: bool = True
    log_level: str = "DEBUG"

    @classmethod
    def load(cls) -> "Settings":
        APP_DIR.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            allowed = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**allowed)
        except FileNotFoundError:
            return cls()
        except Exception:
            return cls()

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        tmp.replace(CONFIG_PATH)
