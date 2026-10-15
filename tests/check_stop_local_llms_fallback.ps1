# CIM access denied: only a fresh PID record for the exact project executable may be stopped.
param([switch]$WrongExecutable, [switch]$StaleRecord)
$script:stopped = @()
$script:running = $true
$script:started = Get-Date
$script:pidRecord = [pscustomobject]@{
    BaseName = 'gemma'
    FullName = 'C:\qa\gemma.pid'
    LastWriteTime = $(if ($StaleRecord) { $script:started.AddMinutes(-10) } else { $script:started.AddSeconds(1) })
}
function Get-Command { [pscustomobject]@{ Source = 'C:\qa\llama-server.exe' } }
function Test-Path { $true }
function Get-CimInstance { throw 'access denied' }
function Get-ChildItem { @($script:pidRecord) }
function Get-Content { '123' }
function Get-Process {
    if (!$script:running) { return $null }
    [pscustomobject]@{
        Id = 123
        Name = 'llama-server'
        Path = $(if ($WrongExecutable) { 'C:\other\llama-server.exe' } else { 'C:\qa\llama-server.exe' })
        StartTime = $script:started
    }
}
function Stop-Process {
    param($Id, [switch]$Force)
    $script:stopped += $Id
    $script:running = $false
}
function Remove-Item {}
$env:SONG_AI_LLAMA_SERVER_COMMAND='C:\qa\llama-server.exe'
$env:SONG_AI_GEMMA_GGUF_PATH='C:\qa\gemma.gguf'
$env:SONG_AI_QWEN_GGUF_PATH='C:\qa\qwen.gguf'
if ($WrongExecutable -or $StaleRecord) {
    try { . (Join-Path $PSScriptRoot '..\scripts\stop-local-llms.ps1') }
    catch {
        if ($script:stopped.Count -ne 0) { throw 'Se detuvo un proceso ajeno.' }
        Write-Output 'PASS: CIM denegado y PID ajeno o antiguo conservado.'
        return
    }
    throw 'Debio bloquear el PID ajeno.'
}
. (Join-Path $PSScriptRoot '..\scripts\stop-local-llms.ps1')
if ($script:stopped.Count -ne 1 -or $script:stopped[0] -ne 123) { throw 'No se detuvo solo el PID verificado.' }
Write-Output 'PASS: CIM denegado y PID del proyecto cerrado.'
