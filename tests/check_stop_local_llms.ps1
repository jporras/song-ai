# Contrato del cierre: proceso del proyecto sin PID, proceso ajeno y fallo de cierre.
param([switch]$FailStop)
$script:stopped = @()
function Get-Command { [pscustomobject]@{ Source = 'C:\qa\llama-server.exe' } }
function Test-Path { $false }
function Get-CimInstance {
    @(
        [pscustomobject]@{ ProcessId=123; ExecutablePath='C:\qa\llama-server.exe'; CommandLine='server -m C:\qa\gemma.gguf' },
        [pscustomobject]@{ ProcessId=456; ExecutablePath='C:\qa\llama-server.exe'; CommandLine='server -m C:\other\model.gguf' },
        [pscustomobject]@{ ProcessId=789; ExecutablePath='C:\other\llama-server.exe'; CommandLine='server -m C:\qa\gemma.gguf' }
    )
}
function Stop-Process {
    param($Id, [switch]$Force)
    if ($FailStop) { throw 'simulated stop failure' }
    $script:stopped += $Id
}
function Get-Process { $null }
$env:SONG_AI_LLAMA_SERVER_COMMAND='C:\qa\llama-server.exe'
$env:SONG_AI_GEMMA_GGUF_PATH='C:\qa\gemma.gguf'
$env:SONG_AI_QWEN_GGUF_PATH='C:\qa\qwen.gguf'
. (Join-Path $PSScriptRoot '..\scripts\stop-local-llms.ps1')
if ($script:stopped.Count -ne 1 -or $script:stopped[0] -ne 123) { throw 'El cierre afecto procesos ajenos o ignoro un servidor sin PID.' }
Write-Output 'PASS: cierre sin PID; servidores ajenos conservados.'
