param(
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $Root "data\runtime\llm"

if (!(Test-Path $RuntimeDir)) {
    Write-Host "[LLM] No hay runtime local de LLM para detener."
    exit 0
}

Get-ChildItem -Path $RuntimeDir -Filter "*.pid" | ForEach-Object {
    $role = $_.BaseName
    $pidValue = (Get-Content -Path $_.FullName -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (!$pidValue) { return }
    $processId = [int]$pidValue
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    if ($null -eq $process) {
        Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
        Write-Host "[LLM] $role ya estaba detenido."
        return
    }
    Write-Host "[LLM] Deteniendo $role pid=$processId"
    & taskkill.exe /PID $processId /T /F | Out-Null
    Remove-Item -LiteralPath $_.FullName -Force -ErrorAction SilentlyContinue
}

if ($Force) {
    Get-Process | Where-Object { $_.ProcessName -like "llama*" } | ForEach-Object {
        Write-Host "[LLM] Forzando cierre de $($_.ProcessName) pid=$($_.Id)"
        & taskkill.exe /PID $_.Id /T /F | Out-Null
    }
}
