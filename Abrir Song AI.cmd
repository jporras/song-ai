@echo off
setlocal
set "SONG_AI_ROOT=%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SONG_AI_ROOT%scripts\open-song-ai.ps1"
if errorlevel 1 (
  echo.
  echo Song AI no pudo abrirse. Revisa el mensaje anterior.
  pause
)
