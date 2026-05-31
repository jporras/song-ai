param(
    [switch]$SkipAudioDeps,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if (!(Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
}

New-Item -ItemType Directory -Force -Path data, data\models, data\providers | Out-Null

if (!(Test-Path ".venv")) {
    py -3.11 -m venv .venv
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

& $Python -m pip install --upgrade pip
& $Pip install -r backend\requirements.txt

if (!$SkipAudioDeps) {
    & $Pip install -r backend\requirements-local-audio.txt
    $env:PYTHONPATH = Join-Path $Root "backend"
    $env:SONG_AI_BOOTSTRAP_ON_START = "true"
    $env:SONG_AI_INSTALL_LOCAL_AUDIO_DEPS = "true"
    $env:SONG_AI_INSTALL_ACE_STEP = "true"
    & $Python -c "from bootstrap.local_bootstrap import run_bootstrap; print(run_bootstrap(force=True))"
}

if (!$SkipFrontend) {
    Push-Location frontend
    npm install
    npm run build
    Pop-Location
}

Write-Host ""
Write-Host "Song AI local preparado."
Write-Host "Ejecuta: scripts\run-local.ps1"
