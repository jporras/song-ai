param(
    [int]$Port = 8000,
    [switch]$NoBootstrap
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$FfmpegCandidates = @(
    "$(Join-Path $Root 'data\tools\ffmpeg\bin')",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build-shared\bin",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin"
)
foreach ($candidate in $FfmpegCandidates) {
    $exists = $false
    try {
        $exists = Test-Path (Join-Path $candidate "ffmpeg.exe")
    } catch {
        $exists = $false
    }
    if ($exists -and (($env:PATH -split ";") -notcontains $candidate)) {
        $env:PATH = "$candidate;$env:PATH"
        break
    }
}

if (!(Test-Path ".venv\Scripts\python.exe")) {
    throw "No existe .venv. Ejecuta scripts\setup-local.ps1 primero."
}

if ($NoBootstrap) {
    $env:SONG_AI_BOOTSTRAP_ON_START = "false"
}

$env:PYTHONPATH = Join-Path $Root "backend"
$env:SONG_AI_MODEL_ROOT = if ($env:SONG_AI_MODEL_ROOT) { $env:SONG_AI_MODEL_ROOT } else { "data/models" }
$env:SONG_AI_PROVIDER_ROOT = if ($env:SONG_AI_PROVIDER_ROOT) { $env:SONG_AI_PROVIDER_ROOT } else { "data/providers" }

& ".venv\Scripts\python.exe" -m uvicorn adapters.http.fastapi_app:app --app-dir backend --host 127.0.0.1 --port $Port
