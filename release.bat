@echo off
setlocal
echo Building GSN Print Service...
python -m PyInstaller --clean --noconfirm --distpath dist gsn_print_service.spec
if errorlevel 1 exit /b 1
echo.
echo Build OK: dist\gsn-print-service\
echo.
echo Next: open installer\setup.iss in Inno Setup and compile to generate the setup EXE.
echo Homologation without printer:
echo   python tools\mock_websocket_server.py --auto-print
echo   python -m app.main --tray
endlocal
