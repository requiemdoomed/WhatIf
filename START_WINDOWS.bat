@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 run.py %*
) else (
  python run.py %*
)
if errorlevel 1 (
  echo.
  echo WhatIf could not start. Read the message above and README.md.
  pause
)
endlocal
