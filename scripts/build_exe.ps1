# Optional: build YuEStudio.exe (single file, windowed) into the install folder.
# The exe only contains the UI + API server; it runs the models with .venv, models\ and tools\ beside it.
# start.bat does the same job without building anything.
$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)
$py = ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { Write-Host "Run install.bat first."; exit 1 }
& tools\uv\uv.exe pip install -p $py pyinstaller==6.22.3 --default-index https://pypi.tuna.tsinghua.edu.cn/simple
if (-not (Test-Path build\icon.ico)) { & $py scripts\make_icon.py }
& $py -m PyInstaller --noconfirm --clean --onefile --windowed --name YuEStudio `
    --icon "$PWD\build\icon.ico" `
    --add-data "$PWD\web;web" --add-data "$PWD\studio\flow.json;studio" --add-data "$PWD\studio\style_guide.md;studio" `
    --collect-submodules uvicorn --collect-submodules webview --collect-submodules mcp.server --collect-submodules mcp.shared --hidden-import mcp.types --collect-submodules sse_starlette --collect-submodules pydantic_settings `
    --workpath build\work --specpath build --distpath build\dist `
    launcher.py
if ($LASTEXITCODE -ne 0) { Write-Host "BUILD FAILED"; exit 1 }
Copy-Item build\dist\YuEStudio.exe .\YuEStudio.exe -Force
Write-Host "BUILT $(Resolve-Path .\YuEStudio.exe)"
