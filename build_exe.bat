@echo off
cd /d "%~dp0"
.venv\Scripts\python.exe -m PyInstaller main.py ^
  --name TempoExtractorAI ^
  --windowed ^
  --onedir ^
  --noconfirm ^
  --collect-all madmom ^
  --collect-all imageio_ffmpeg ^
  --collect-all matplotlib ^
  --collect-all mido
