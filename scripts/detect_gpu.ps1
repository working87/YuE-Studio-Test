# Detect the NVIDIA GPU and decide whether / how YuE Studio can run on it.
#   powershell -ExecutionPolicy Bypass -File scripts\detect_gpu.ps1          # human-readable
#   powershell -ExecutionPolicy Bypass -File scripts\detect_gpu.ps1 -Json    # for agents and install.ps1
# The -Simulate* parameters test the rules for other cards without having them.
param(
    [switch]$Json,
    [string]$SimulateName,
    [double]$SimulateMemoryGB = 0,
    [string]$SimulateDriver,
    [string]$SimulateComputeCap
)

$MinDriver = 570          # torch 2.10 + CUDA 12.8 wheels
$MinComputeCap = 7.0      # the wheels ship kernels for sm_70 .. sm_120
$Fp8ComputeCap = 8.9      # YuE2's FP8 mode (12 GB profile) needs RTX 40 / 50

function Result($ok, $tier, $profile, $level, $message, $gpu) {
    [ordered]@{
        ok = $ok; tier = $tier; profile = $profile; level = $level; message = $message;
        gpu = $gpu
    }
}

$gpu = $null
if ($SimulateName) {
    $gpu = [ordered]@{ name = $SimulateName; memory_gb = $SimulateMemoryGB; driver = $SimulateDriver; compute_cap = $SimulateComputeCap; count = 1; simulated = $true }
} else {
    $smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($smi) {
        $lines = & nvidia-smi --query-gpu=name,memory.total,driver_version,compute_cap --format=csv,noheader,nounits 2>$null
        if ($LASTEXITCODE -eq 0 -and $lines) {
            $rows = @($lines | ForEach-Object { $p = $_ -split ',\s*'; [ordered]@{ name = $p[0].Trim(); memory_gb = [math]::Round([double]$p[1] / 1024, 1); driver = $p[2].Trim(); compute_cap = $p[3].Trim() } })
            # The app runs on GPU 0 (CUDA's default device).
            $gpu = $rows[0]
            $gpu.count = $rows.Count
            $gpu.simulated = $false
        }
    }
}

if (-not $gpu) {
    $r = Result $false "none" $null "error" "未检测到 NVIDIA 显卡或驱动（找不到 nvidia-smi）。YuE Studio 需要 NVIDIA 显卡，请先到 https://www.nvidia.cn/drivers 安装最新驱动。" $null
} else {
    $driverMajor = [int](($gpu.driver -split '\.')[0])
    $cap = [double]$gpu.compute_cap
    $mem = [double]$gpu.memory_gb
    if ($driverMajor -lt $MinDriver) {
        $r = Result $false "driver" $null "error" "显卡驱动 $($gpu.driver) 太旧，需要 $MinDriver 或更新（支持 CUDA 12.8）。请到 https://www.nvidia.cn/drivers 更新驱动后重试。" $gpu
    } elseif ($cap -lt $MinComputeCap) {
        $r = Result $false "arch" $null "error" "$($gpu.name)（算力 $($gpu.compute_cap)）太老：PyTorch 2.10 只支持 RTX 20 系 / Volta 及更新的显卡。" $gpu
    } elseif ($mem -lt 11.5) {
        $r = Result $false "low-vram" $null "error" "$($gpu.name) 只有 $mem GB 显存，官方 PyTorch 版 YuE2 至少需要约 12 GB。8 GB 显卡可以关注社区的 GGUF 量化版（见 README「8GB 显卡」），本项目暂未集成。" $gpu
    } else {
        if ($mem -ge 23) { $tier = "24g"; $profile = "24g"; $level = "ok"; $msg = "显存充足，使用官方无损配置（最快）。" }
        elseif ($mem -ge 15) { $tier = "16g"; $profile = "16g"; $level = "ok"; $msg = "16 GB 级显卡，使用无损配置；显存被其他程序占用时自动改用省显存模式。" }
        elseif ($cap -ge $Fp8ComputeCap) { $tier = "12g"; $profile = "12g"; $level = "warn"; $msg = "12 GB 级显卡：使用 FP8 量化 + 卸载，能出歌但很慢（30 秒的歌约 2 分钟）。" }
        else { $tier = "12g"; $profile = "12g-safe"; $level = "warn"; $msg = "12 GB 级显卡（不支持 FP8）：使用无损 + 卸载，实验性，作者没有在这类显卡上测试过，可能很慢或显存不足。" }
        if ($cap -lt 8.0) { $level = "warn"; $msg += " 注意：RTX 20 系 / Volta 没有原生 BF16，速度可能明显变慢，未经测试。" }
        if ($gpu.count -gt 1) { $msg += " 检测到 $($gpu.count) 张显卡，程序使用第 1 张。" }
        $r = Result $true $tier $profile $level $msg $gpu
    }
}

if ($Json) {
    $r | ConvertTo-Json -Depth 4 -Compress
} else {
    if ($r.gpu) { Write-Host ("显卡：{0}，{1} GB 显存，驱动 {2}，算力 {3}" -f $r.gpu.name, $r.gpu.memory_gb, $r.gpu.driver, $r.gpu.compute_cap) }
    $color = @{ ok = "Green"; warn = "Yellow"; error = "Red" }[$r.level]
    Write-Host $r.message -ForegroundColor $color
    if ($r.ok) { Write-Host "档位：$($r.profile)" }
}
if (-not $r.ok) { exit 1 }
