@echo off
python -m PyInstaller --clean --noconfirm gsn_print_service.spec
if errorlevel 1 exit /b 1
