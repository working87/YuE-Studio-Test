@echo off
rem Open the YuE Studio desktop window (run install.bat first).
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo YuE Studio is not installed yet. Double-click install.bat first.
    pause
    exit /b 1
)
start "" ".venv\Scripts\pythonw.exe" -m studio desktop
