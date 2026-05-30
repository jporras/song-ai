param(
    [switch]$InstallFfmpeg,
    [switch]$SkipAceStep,
    [switch]$SkipFrontend
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

if ($InstallFfmpeg) {
    $ffmpeg = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if (!$ffmpeg) {
        $winget = Get-Command winget -ErrorAction SilentlyContinue
        if (!$winget) {
            throw "winget no esta disponible. Instala ffmpeg manualmente y agrega su carpeta bin al PATH."
        }
        winget install --id Gyan.FFmpeg.Shared -e --accept-package-agreements --accept-source-agreements
        Write-Host "Si ffmpeg aun no aparece en PATH, cierra y abre la terminal."
    }
}

if ($SkipAceStep) {
    & (Join-Path $Root "scripts\setup-local.ps1") -SkipAudioDeps -SkipFrontend:$SkipFrontend
} else {
    & (Join-Path $Root "scripts\setup-local.ps1") -SkipFrontend:$SkipFrontend
}

& (Join-Path $Root "scripts\check-local-prereqs.ps1")
