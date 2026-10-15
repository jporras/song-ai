# CIM denied without PID records: closed project ports permit continuation, open ports block.
param([switch]$PortOpen)
$listener = $null
try {
    if ($PortOpen) {
        $listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, 0)
        $listener.Start()
        $port = $listener.LocalEndpoint.Port
    } else {
        $port = 1
    }
    function Get-Command { [pscustomobject]@{ Source = 'C:\qa\llama-server.exe' } }
    function Get-CimInstance { throw 'access denied' }
    function Get-ChildItem { @() }
    $env:SONG_AI_LLAMA_SERVER_COMMAND='C:\qa\llama-server.exe'
    $env:SONG_AI_GEMMA_GGUF_PATH='C:\qa\gemma.gguf'
    $env:SONG_AI_QWEN_GGUF_PATH='C:\qa\qwen.gguf'
    $env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL="http://127.0.0.1:$port"
    $env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL='http://127.0.0.1:1'
    if ($PortOpen) {
        try { . (Join-Path $PSScriptRoot '..\scripts\stop-local-llms.ps1') }
        catch { Write-Output 'PASS: CIM denegado y puerto sin PID bloqueado.'; return }
        throw 'Debio bloquear el puerto abierto sin PID.'
    }
    . (Join-Path $PSScriptRoot '..\scripts\stop-local-llms.ps1')
    Write-Output 'PASS: CIM denegado sin PID ni puertos activos.'
} finally {
    if ($listener) { $listener.Stop() }
}
