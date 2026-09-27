@echo off
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -File "%~dp0install_context_menu.ps1"
pause
