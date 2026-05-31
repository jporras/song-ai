param(
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Requirements = Join-Path $Root "backend\requirements-intel-xpu.txt"

Write-Host "Song-AI Intel XPU prerequisitos"
Write-Host "================================"
Write-Host "Antes de instalar paquetes Python:"
Write-Host "1. Actualiza el driver Intel Graphics desde Intel Driver & Support Assistant o el fabricante del equipo."
Write-Host "2. Reinicia Windows despues del driver."
Write-Host "3. Ejecuta: .\.venv\Scripts\python.exe tools\check_xpu_stack.py --probe-tensor"
Write-Host ""

if (-not (Test-Path $Python)) {
    throw "No existe .venv\Scripts\python.exe. Ejecuta scripts\setup-local.ps1 primero."
}

$installCommand = @(
    "`"$Python`"",
    "-m",
    "pip",
    "install",
    "--upgrade",
    "--force-reinstall",
    "-r",
    "`"$Requirements`""
) -join " "

Write-Host "Comando de instalacion XPU:"
Write-Host $installCommand
Write-Host ""

if ($DryRun) {
    Write-Host "DryRun activo: no se instalaron paquetes."
    exit 0
}

Invoke-Expression $installCommand
Write-Host ""
Write-Host "Verificando XPU..."
& $Python tools\check_xpu_stack.py --probe-tensor
