# Development Guide — Crystal Companion

## Running tests

```powershell
python -m compileall -q crystal_agent tests
python -m pytest -q
```

Current tests cover the folder allowlist, text-only extension guard, file-size guard, and basic listing. They do **not** test the Qt event loop, a real Ollama server, model downloads, audio hardware, or the Windows compositor.

## Development recommendations

From the README:

1. Keep network/model work out of the Qt UI thread. Use worker threads and signal results back to widgets.
2. Keep settings schema changes in `config.py`, then wire them into `SettingsWindow` and runtime code.
3. Put all file-system access behind `FolderTools`; do not add an unrestricted `open(path)` call in UI or prompt code.
4. Use `logging` rather than bare `print()` for new subsystems, and surface actionable errors in the UI.
5. Avoid importing Torch/Transformers during application startup; lazy-load them so the orb can appear quickly.
6. Add tests for every file permission boundary and error path.
7. Treat file contents and model output as untrusted. Never directly execute text emitted by an LLM.

## Worker pattern (for adding new async work)

```python
from crystal_agent.ui.windows import Worker, WorkerSignals
from PySide6.QtCore import QRunnable, QObject, Signal

# Wrap a function in a Worker and start it on the global thread pool
worker = Worker(lambda: some_blocking_function())
worker.signals.result.connect(lambda answer: handle_result(answer))
worker.signals.error.connect(handle_error)
app.pool.start(worker)  # QThreadPool.globalInstance()
```

## Settings changes

1. Add the field to the `Settings` dataclass in `crystal_agent/config.py` (and/or `crystal_agent/ui/config.py` for UI-specific fields)
2. Wire it into `SettingsWindow` (add a form row in the appropriate tab)
3. Add it to `SettingsWindow.collect()` so it's read back on save
4. Apply it in `CompanionApp.apply_settings()` if it affects runtime behavior

## Adding file tools

All file-system access should go through `FolderTools` in `crystal_agent/tools.py`. To add a new tool:

1. Add a method to `FolderTools` with path validation via `_safe()`
2. Add an intent regex in `OllamaAgent._maybe_use_file_tool()` in `crystal_agent/agent.py`
3. Add a test in `tests/test_tools.py` covering the allowlist boundary

## Logging

Use `logging.getLogger("crystal")` for new subsystems. The logger is configured by `logging_setup.configure_logging()` with rotating file + console output.

## Related notes

- [[module-map]] — module locations
- [[architecture]] — threading model
- [[tools-and-permissions]] — FolderTools contract
- [[configuration-reference]] — settings schema
- [[security-and-privacy]] — security boundaries to respect