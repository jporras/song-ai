param(
    [int]$ApiPort = 8000,
    [int]$UiPort = 5173
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$FfmpegCandidates = @(
    "$(Join-Path $Root 'data\tools\ffmpeg\bin')",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build-shared\bin",
    "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin"
)
$FfmpegPathPrefix = ""
foreach ($candidate in $FfmpegCandidates) {
    $exists = $false
    try {
        $exists = Test-Path (Join-Path $candidate "ffmpeg.exe")
    } catch {
        $exists = $false
    }
    if ($exists) {
        $FfmpegPathPrefix = "`$env:PATH='$candidate;' + `$env:PATH; "
        break
    }
}

if (!(Test-Path ".venv\Scripts\python.exe")) {
    throw "No existe .venv. Ejecuta scripts\setup-local.ps1 primero."
}

$Backend = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Root'; $FfmpegPathPrefix`$env:PYTHONPATH='$Root\backend'; .\.venv\Scripts\python.exe -m uvicorn adapters.http.fastapi_app:app --app-dir backend --host 127.0.0.1 --port $ApiPort"
) -PassThru -WindowStyle Hidden

Push-Location frontend
$Frontend = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$Root\frontend'; npm run dev -- --host 127.0.0.1 --port $UiPort"
) -PassThru -WindowStyle Hidden
Pop-Location

Write-Host "Backend PID: $($Backend.Id) http://127.0.0.1:$ApiPort"
Write-Host "Frontend PID: $($Frontend.Id) http://127.0.0.1:$UiPort"
