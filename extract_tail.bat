@echo off
setlocal
set "IN=%~1"
if "%IN%"=="" exit /b 1
if not exist "%IN%" exit /b 1
set "OUT=%~dp1%~n1_尾帧.png"
"%~dp0ffmpeg.exe" -y -sseof -0.1 -i "%IN%" -frames:v 1 -q:v 2 "%OUT%" >nul 2>&1
if exist "%OUT%" (
  explorer "%~dp1"
  exit /b 0
) else (
  powershell -NoProfile -Command "Add-Type -AssemblyName System.Windows.Forms;[System.Windows.Forms.MessageBox]::Show('Tail frame extraction failed. Please check the video file.','Error')"
  exit /b 1
)
endlocal
