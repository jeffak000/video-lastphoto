@echo off
cd /d "%~dp0"
py video_tailframe.py
if errorlevel 1 pause
