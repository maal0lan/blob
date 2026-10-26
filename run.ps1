$ErrorActionPreference = 'Stop'
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Virtual environment not found. Run .\setup.ps1 first.' }
& .\.venv\Scripts\python.exe -m crystal_agent
