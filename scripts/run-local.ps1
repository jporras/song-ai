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
$StartLlmsScript = Join-Path $Root "scripts\start-local-llms.ps1"
$StopLlmsScript = Join-Path $Root "scripts\stop-local-llms.ps1"
$env:SONG_AI_START_LLM_COMMAND = if ($env:SONG_AI_START_LLM_COMMAND) { $env:SONG_AI_START_LLM_COMMAND } else { "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$StartLlmsScript`"" }
$env:SONG_AI_STOP_LLM_COMMAND = if ($env:SONG_AI_STOP_LLM_COMMAND) { $env:SONG_AI_STOP_LLM_COMMAND } else { "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$StopLlmsScript`"" }
$env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL = if ($env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL) { $env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL } else { "http://localhost:8081" }
$env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL = if ($env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL) { $env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL } else { "http://localhost:8082" }
$env:SONG_AI_LLAMA_CPP_GPU_ARGS = if ($env:SONG_AI_LLAMA_CPP_GPU_ARGS) { $env:SONG_AI_LLAMA_CPP_GPU_ARGS } else { "--n-gpu-layers 999" }

try {
    & ".venv\Scripts\python.exe" -m uvicorn adapters.http.fastapi_app:app --app-dir backend --host 127.0.0.1 --port $Port
} finally {
    $StopOnExit = if ($env:SONG_AI_STOP_LLM_ON_EXIT) { $env:SONG_AI_STOP_LLM_ON_EXIT } else { "true" }
    if ($StopOnExit.Trim().ToLowerInvariant() -in @("1", "true", "yes", "on")) {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopLlmsScript
    }
}
