# Setup and Deployment — Crystal Companion

## Files

| File | Purpose |
|---|---|
| `setup.ps1` | One-time setup: create venv, upgrade pip, install requirements, editable install |
| `run.ps1` | Launch: verify venv exists, run `python -m crystal_agent` |
| `requirements.txt` | Python dependencies |
| `pyproject.toml` | Packaging config (setuptools, pytest) |
| `.env.example` | Optional startup override (`CRYSTAL_LOG_LEVEL=DEBUG`) |

## Requirements

- Windows 10/11 (primary target)
- Python 3.11 or 3.12 recommended
- Ollama installed and running locally (`http://127.0.0.1:11434`)
- At least one Ollama model downloaded
- Disk space for Python packages, PyTorch, and the TTS model cache
- Working speaker/audio output for TTS
- Optional GPU: PyTorch/Transformers may use an available accelerator; `device_map=auto` decides placement

## Setup steps (Windows PowerShell)

```powershell
# 1. Create virtual environment
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Install and start Ollama
ollama --version
ollama list
ollama pull lfm2.5:350m   # or another model

# 4. Verify Ollama responds
Invoke-RestMethod http://127.0.0.1:11434/api/tags

# 5. Start Crystal
python -m crystal_agent
```

Or use the scripts: `.\setup.ps1` once, then `.\run.ps1` for subsequent launches.

## First launch

1. Right-click the orb → Settings (or use tray → Settings)
2. Under Models & Voice, set the Ollama endpoint and model names
3. Click "Test Ollama" to verify connectivity and inspect installed model names
4. Choose fast or reasoning model mode
5. Keep TTS enabled if you want spoken responses (accept Phonon HF terms on first load)
6. For local file access, go to Folder Access, add folders, and explicitly enable folder access
7. Click "Save settings"
8. Click the orb and ask a question

## Important notes

- PyTorch installation can be large and accelerator-specific. If pip chooses an unsuitable build, use the official PyTorch install selector for your CPU/CUDA setup, then install remaining requirements.
- The pinned Transformers revision is required because Phonon uses `AutoModelForTextToWaveform`, which may not exist in a standard released Transformers build.
- A model tag may be unavailable or named differently in your Ollama catalogue. Use the exact tag from `ollama list`.
- The app does not open a browser or start a web server.
- The app does not silently download LLMs itself.

## Packaging

No packaging yet — this is a source-run Python app, not an installer or signed executable. See roadmap item 10 for PyInstaller packaging.

## Related notes

- [[project-overview]] — high-level summary
- [[configuration-reference]] — all settings and defaults
- [[module-map]] — module locations
- [[security-and-privacy]] — security considerations for deployment