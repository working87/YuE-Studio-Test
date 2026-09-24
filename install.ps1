# YuE Studio installer (Windows 10/11 + NVIDIA GPU). Double-click install.bat, or:
#   powershell -ExecutionPolicy Bypass -File install.ps1 [-SkipModels] [-Force] [-ModelSource modelscope|hf]
#
# Everything is downloaded through mirrors that work in mainland China without a proxy:
#   uv (Tsinghua PyPI) -> Python 3.12 (npmmirror) -> packages (Tsinghua PyPI) + torch/torchaudio (Aliyun)
#   -> FFmpeg (imageio-ffmpeg from Tsinghua PyPI) -> models (ModelScope)
# All of it lands inside this folder (tools\, .venv\, models\); nothing is installed system-wide.
# Safe to re-run: finished steps are skipped and model downloads resume.
param(
    [switch]$SkipModels,
    [switch]$Force,
    [ValidateSet("modelscope", "hf")][string]$ModelSource = "modelscope"
)

$ErrorActionPreference = "Continue"   # uv writes progress to stderr
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Root = $PSScriptRoot
Set-Location $Root

$UvVersion = "0.12.18"
$PythonVersion = "3.12"
$PyPI = "https://pypi.tuna.tsinghua.edu.cn/simple"
$TorchLinks = "https://mirrors.aliyun.com/pytorch-wheels/cu128/"
$PythonMirror = "https://registry.npmmirror.com/-/binary/python-build-standalone"
$Venv = Join-Path $Root ".venv"
$Py = Join-Path $Venv "Scripts\python.exe"

New-Item -ItemType Directory -Force (Join-Path $Root "tools") | Out-Null
Start-Transcript -Path (Join-Path $Root "install.log") -Append | Out-Null

function Step($text) { Write-Host ""; Write-Host "== $text" -ForegroundColor Cyan }
function Fail($text) { Write-Host ""; Write-Host "安装失败：$text" -ForegroundColor Red; Write-Host "完整日志：$Root\install.log"; Stop-Transcript | Out-Null; exit 1 }
function Check($what) { if ($LASTEXITCODE -ne 0) { Fail $what } }

# ---------------------------------------------------------------- 1. GPU
Step "1/6 检测显卡"
$gpuJson = & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Root "scripts\detect_gpu.ps1") -Json
$gpu = $gpuJson | ConvertFrom-Json
if ($gpu.gpu) { Write-Host ("{0}，{1} GB 显存，驱动 {2}，算力 {3}" -f $gpu.gpu.name, $gpu.gpu.memory_gb, $gpu.gpu.driver, $gpu.gpu.compute_cap) }
if (-not $gpu.ok) {
    Write-Host $gpu.message -ForegroundColor Red
    if (-not $Force) { Fail "这台电脑的显卡不满足要求（确定要继续可以加 -Force）" }
    Write-Host "已指定 -Force，继续安装。" -ForegroundColor Yellow
} else {
    $color = if ($gpu.level -eq "ok") { "Green" } else { "Yellow" }
    Write-Host "$($gpu.message)（档位 $($gpu.profile)）" -ForegroundColor $color
}
$free = (Get-PSDrive ($Root.Substring(0, 1))).Free / 1GB
if ($free -lt 30) { Write-Host ("磁盘剩余 {0:N0} GB；完整安装约需 25 GB（环境约 7 GB + 模型约 10 GB + 下载缓存）。" -f $free) -ForegroundColor Yellow }

# ---------------------------------------------------------------- 2. uv
Step "2/6 准备 uv（Python 包管理器，清华 PyPI 镜像）"
$Uv = Join-Path $Root "tools\uv\uv.exe"
if (-not (Test-Path $Uv)) {
    $index = "$PyPI/uv/"
    try { $html = (Invoke-WebRequest $index -UseBasicParsing -TimeoutSec 60).Content } catch { Fail "无法访问 $index ：$($_.Exception.Message)" }
    $name = "uv-$UvVersion-py3-none-win_amd64.whl"
    $m = [regex]::Match($html, 'href="([^"#]*' + [regex]::Escape($name) + ')')
    if (-not $m.Success) { Fail "镜像上找不到 $name" }
    $url = [Uri]::new([Uri]$index, $m.Groups[1].Value).AbsoluteUri
    $tmp = Join-Path $env:TEMP "yue-studio-uv"
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory $tmp | Out-Null
    try { Invoke-WebRequest $url -OutFile "$tmp\uv.zip" -UseBasicParsing -TimeoutSec 300 } catch { Fail "下载 uv 失败：$($_.Exception.Message)" }
    Expand-Archive "$tmp\uv.zip" "$tmp\x" -Force
    $exe = Get-ChildItem "$tmp\x" -Recurse -Filter uv.exe | Select-Object -First 1
    if (-not $exe) { Fail "uv 安装包里没有 uv.exe" }
    New-Item -ItemType Directory -Force (Split-Path $Uv) | Out-Null
    Copy-Item $exe.FullName $Uv
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
& $Uv --version
Check "uv 无法运行"

# Everything uv does from here on stays on mirrors and inside this folder.
$env:UV_DEFAULT_INDEX = $PyPI
$env:UV_PYTHON_INSTALL_MIRROR = $PythonMirror
$env:UV_PYTHON_INSTALL_DIR = Join-Path $Root "tools\python"
$env:UV_PYTHON_PREFERENCE = "only-managed"
$env:UV_HTTP_TIMEOUT = "300"
$env:UV_LINK_MODE = "copy"
$env:UV_NO_CONFIG = "1"            # ignore any personal uv.toml that could point elsewhere

# ---------------------------------------------------------------- 3. Python + packages
Step "3/6 创建 Python $PythonVersion 环境并安装依赖（torch 约 3 GB，第一次需要几分钟）"
if (-not (Test-Path $Py)) {
    & $Uv venv $Venv --python $PythonVersion
    Check "创建 Python 环境失败（Python 从 npmmirror 下载）"
}
& $Uv pip install -p $Py -r requirements.txt --find-links $TorchLinks
Check "安装依赖失败（见上方 uv 的报错；如果是网络超时，重新运行 install.bat 即可）"
& $Py scripts\patch_windows.py
Check "给 YuE2 打 Windows 补丁失败"

# ---------------------------------------------------------------- 4. FFmpeg
Step "4/6 准备 FFmpeg"
$ffDir = Join-Path $Root "tools\ffmpeg"
if (-not (Test-Path "$ffDir\ffmpeg.exe")) {
    New-Item -ItemType Directory -Force $ffDir | Out-Null
    & $Py -c "import imageio_ffmpeg, shutil, sys; shutil.copy(imageio_ffmpeg.get_ffmpeg_exe(), sys.argv[1])" "$ffDir\ffmpeg.exe"
    Check "复制 FFmpeg 失败"
}
& "$ffDir\ffmpeg.exe" -hide_banner -version | Select-Object -First 1

# ---------------------------------------------------------------- 5. GPU check inside the environment
Step "5/6 检查 PyTorch 能否使用显卡"
& $Py -c "import torch; ok = torch.cuda.is_available(); print('torch', torch.__version__, 'CUDA', torch.version.cuda, 'available' if ok else 'NOT available'); ok or exit(1); arch = 'sm_%d%d' % torch.cuda.get_device_capability(0); print(torch.cuda.get_device_name(0), arch, 'supported' if arch in torch.cuda.get_arch_list() else 'NOT in ' + str(torch.cuda.get_arch_list()))"
if ($LASTEXITCODE -ne 0 -and -not $Force) { Fail "PyTorch 用不了显卡。请更新 NVIDIA 驱动（570 或更新）后重新运行" }

# ---------------------------------------------------------------- 6. models
if ($SkipModels) {
    Step "6/6 跳过模型下载（-SkipModels）"
} else {
    Step "6/6 下载模型（约 10 GB，来源 $ModelSource，断了重新运行会续传）"
    & $Py scripts\download_models.py --source $ModelSource
    Check "模型下载没有完成；重新运行 install.bat 会从断点继续"
}

Step "自检"
& $Py -m studio doctor
$doctorOk = $LASTEXITCODE -eq 0
Stop-Transcript | Out-Null
Write-Host ""
if ($doctorOk) {
    Write-Host "安装完成。双击 start.bat 打开 YuE Studio。" -ForegroundColor Green
} else {
    Write-Host "安装步骤已执行完，但自检有未通过的项目（见上方）。" -ForegroundColor Yellow
    if (-not $SkipModels) { exit 1 }
}
