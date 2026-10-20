@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -m unittest discover -s tests -v
) else (
  python -m unittest discover -s tests -v
)
echo.
echo If any test failed, review the error above before presenting the app.
pause
endlocal
