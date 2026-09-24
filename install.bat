@echo off
rem Double-click to install YuE Studio (see README). Extra arguments go to install.ps1, e.g. install.bat -SkipModels
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
pause
