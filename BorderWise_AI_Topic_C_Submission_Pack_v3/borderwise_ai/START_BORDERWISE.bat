@echo off
setlocal
cd /d "%~dp0"
title BorderWise AI - Local App

echo ==============================================================
echo  BorderWise AI - Topic C Student Finance Assistant
echo ==============================================================
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  py --version
  py server.py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python --version
    python server.py
  ) else (
    echo Python was not found.
    echo Install Python 3.10 or newer from https://www.python.org/downloads/
    echo During installation, enable Add Python to PATH.
  )
)
echo.
echo BorderWise stopped. Press any key to close this window.
pause >nul
endlocal
