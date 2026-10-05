param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $Root "data\runtime\llm"
$LogDir = Join-Path $Root "data\logs\llm"
New-Item -ItemType Directory -Force -Path $RuntimeDir, $LogDir | Out-Null

function Get-PortFromUrl([string]$Url, [int]$DefaultPort) {
    try {
        $uri = [Uri]$Url
        if ($uri.Port -gt 0) { return $uri.Port }
    } catch {
    }
    return $DefaultPort
}

function Test-PortOpen([int]$Port) {
    try {
        $client = New-Object Net.Sockets.TcpClient
        $async = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        $ready = $async.AsyncWaitHandle.WaitOne(250)
        if ($ready) {
            $client.EndConnect($async)
            $client.Close()
            return $true
        }
        $client.Close()
    } catch {
    }
    return $false
}

function Split-Args([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { return @() }
    return [regex]::Matches($Value, '("[^"]+"|\S+)') | ForEach-Object { $_.Value.Trim('"') }
}

function Start-LlmServer(
    [string]$Role,
    [string]$ModelPath,
    [int]$Port,
    [string]$ExtraArgs
) {
    $pidFile = Join-Path $RuntimeDir "$Role.pid"
    $logFile = Join-Path $LogDir "$Role.out.log"
    $errorLogFile = Join-Path $LogDir "$Role.err.log"
    if (!(Test-Path $ModelPath)) {
        Write-Host "[LLM] $Role omitido: no existe modelo $ModelPath"
        return
    }
    if (!$Force -and (Test-PortOpen $Port)) {
        Write-Host "[LLM] $Role ya responde en puerto $Port"
        return
    }

    $bundledServer = Join-Path $Root "data\tools\llama.cpp\llama-server.exe"
    $serverCommand = if ($env:SONG_AI_LLAMA_SERVER_COMMAND) {
        $env:SONG_AI_LLAMA_SERVER_COMMAND
    } elseif (Test-Path $bundledServer) {
        $bundledServer
    } else {
        "llama-server"
    }
    $server = Get-Command $serverCommand -ErrorAction SilentlyContinue
    if ($null -eq $server) {
        Write-Host "[LLM] llama-server no encontrado. Configura SONG_AI_LLAMA_SERVER_COMMAND o agrega llama.cpp al PATH."
        return
    }

    $gpuArgs = if ($env:SONG_AI_LLAMA_CPP_GPU_ARGS) { $env:SONG_AI_LLAMA_CPP_GPU_ARGS } else { "--n-gpu-layers 999" }
    $ctxSize = if ($env:SONG_AI_LLAMA_CPP_CTX_SIZE) { $env:SONG_AI_LLAMA_CPP_CTX_SIZE } else { "4096" }
    $args = @("-m", $ModelPath, "--port", "$Port", "--ctx-size", "$ctxSize")
    $args += Split-Args $gpuArgs
    $args += Split-Args $ExtraArgs

    Write-Host "[LLM] Iniciando $Role en puerto $Port con GPU args: $gpuArgs"
    $process = Start-Process -FilePath $server.Source -ArgumentList $args -WorkingDirectory $Root -WindowStyle Hidden -RedirectStandardOutput $logFile -RedirectStandardError $errorLogFile -PassThru
    Set-Content -Path $pidFile -Value $process.Id -Encoding ascii
}

$gemmaUrl = if ($env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL) { $env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL } else { "http://localhost:8081" }
$qwenUrl = if ($env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL) { $env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL } else { "http://localhost:8082" }
$gemmaModel = if ($env:SONG_AI_GEMMA_GGUF_PATH) { $env:SONG_AI_GEMMA_GGUF_PATH } else { Join-Path $Root "data\models\llm\gemma\gemma.gguf" }
$qwenModel = if ($env:SONG_AI_QWEN_GGUF_PATH) { $env:SONG_AI_QWEN_GGUF_PATH } else { Join-Path $Root "data\models\llm\qwen\qwen.gguf" }

Start-LlmServer -Role "gemma" -ModelPath $gemmaModel -Port (Get-PortFromUrl $gemmaUrl 8081) -ExtraArgs $env:SONG_AI_GEMMA_LLAMA_ARGS
Start-LlmServer -Role "qwen" -ModelPath $qwenModel -Port (Get-PortFromUrl $qwenUrl 8082) -ExtraArgs $env:SONG_AI_QWEN_LLAMA_ARGS
