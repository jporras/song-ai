param(
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

function Add-DetectedFfmpegToPath {
    $candidates = @(
        "$(Join-Path $Root 'data\tools\ffmpeg\bin')",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build-shared\bin",
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin"
    )
    foreach ($candidate in $candidates) {
        $exists = $false
        try {
            $exists = Test-Path (Join-Path $candidate "ffmpeg.exe")
        } catch {
            $exists = $false
        }
        if ($exists -and (($env:PATH -split ";") -notcontains $candidate)) {
            $env:PATH = "$candidate;$env:PATH"
            return $candidate
        }
    }
    return ""
}

$DetectedFfmpegBin = Add-DetectedFfmpegToPath

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$checks = [ordered]@{}

$checks.python311 = [ordered]@{
    ok = Test-Path $Python
    detail = if (Test-Path $Python) { (& $Python --version) -join " " } else { "No existe .venv. Ejecuta scripts\setup-local.ps1." }
}

$node = Get-Command node -ErrorAction SilentlyContinue
$npm = Get-Command npm.cmd -ErrorAction SilentlyContinue
$ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue

$checks.node = [ordered]@{
    ok = [bool]$node
    detail = if ($node) { (& node --version) } else { "Node.js no esta en PATH." }
}
$checks.npm = [ordered]@{
    ok = [bool]$npm
    detail = if ($npm) { (& npm.cmd --version) } else { "npm.cmd no esta en PATH." }
}
$checks.ffmpeg = [ordered]@{
    ok = [bool]$ffmpeg
    detail = if ($ffmpeg) { $ffmpeg.Source } elseif ($DetectedFfmpegBin) { $DetectedFfmpegBin } else { "ffmpeg no esta en PATH. Instala ffmpeg o ejecuta scripts\install-local-prereqs.ps1 -InstallFfmpeg." }
}

if (Test-Path $Python) {
    $env:PYTHONPATH = Join-Path $Root "backend"
    $moduleCode = "import importlib.util,json; mods=['fastapi','uvicorn','psutil','torch','torchaudio','torchcodec','soundfile','intel_extension_for_pytorch','acestep']; print(json.dumps({name: importlib.util.find_spec(name) is not None for name in mods}))"
    $moduleJson = & $Python -c $moduleCode
    $modules = $moduleJson | ConvertFrom-Json
    foreach ($name in $modules.PSObject.Properties.Name) {
        $checks["python:$name"] = [ordered]@{
            ok = [bool]$modules.$name
            detail = if ($modules.$name) { "importable" } else { "no importable en .venv" }
        }
    }
    $pipelineCode = "import json,sys; sys.path.insert(0,'backend'); from application.song_service import SongService; from config.settings import Settings; from core.storage import StorageManager; s=Settings.load(); service=SongService(StorageManager(s.data_dir), s); print(json.dumps(service.local_pipeline_status(), ensure_ascii=False))"
    $pipelineJson = & $Python -c $pipelineCode
    $checks.local_pipeline = $pipelineJson | ConvertFrom-Json
    $xpuJson = & $Python tools\check_xpu_stack.py --json
    $checks.intel_xpu = ($xpuJson | ConvertFrom-Json).accelerators
}

if ($Json) {
    $checks | ConvertTo-Json -Depth 8
    exit 0
}

Write-Host "Song AI local prerequisitos"
Write-Host "==========================="
foreach ($entry in $checks.GetEnumerator()) {
    if ($entry.Key -eq "local_pipeline") { continue }
    $status = if ($entry.Value.ok) { "OK" } else { "FALTA" }
    Write-Host ("[{0}] {1}: {2}" -f $status, $entry.Key, $entry.Value.detail)
}

if ($checks.local_pipeline) {
    Write-Host ""
    Write-Host "Pipeline local:"
    Write-Host ("ready: {0}" -f $checks.local_pipeline.ready)
    Write-Host ("missing: {0}" -f (($checks.local_pipeline.missing | ForEach-Object { $_ }) -join ", "))
    foreach ($requirement in $checks.local_pipeline.requirements) {
        Write-Host ("- {0}: {1} - {2}" -f $requirement.role, $requirement.configured, $requirement.detail)
        if ($requirement.role -eq "full_song" -and $requirement.accelerator) {
            Write-Host ("  device: {0} / xpu={1} / cuda={2} / {3}" -f $requirement.device, $requirement.accelerator.xpu_available, $requirement.accelerator.cuda_available, $requirement.accelerator.fallback_reason)
        }
    }
}

if ($checks.intel_xpu) {
    Write-Host ""
    Write-Host "Intel XPU:"
    Write-Host ("torch: {0} ({1})" -f $checks.intel_xpu.torch_importable, $checks.intel_xpu.torch_version)
    Write-Host ("torch.xpu: api={0}, disponible={1}, dispositivos={2}, nombre={3}" -f $checks.intel_xpu.xpu_api_available, $checks.intel_xpu.xpu_available, $checks.intel_xpu.xpu_device_count, $checks.intel_xpu.xpu_device_name)
    Write-Host ("backend recomendado: {0}" -f $checks.intel_xpu.recommended_backend)
    if ($checks.intel_xpu.fallback_reason) {
        Write-Host ("fallback: {0}" -f $checks.intel_xpu.fallback_reason)
    }
}
