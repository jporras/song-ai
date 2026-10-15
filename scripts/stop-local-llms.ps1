param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
. (Join-Path $PSScriptRoot 'llm-environment.ps1')
Import-SongAiEnvironment (Join-Path $Root '.env')
$RuntimeDir = Join-Path $Root "data\runtime\llm"

$serverCommand = if ($env:SONG_AI_LLAMA_SERVER_COMMAND) { $env:SONG_AI_LLAMA_SERVER_COMMAND } else { Join-Path $Root "data\tools\llama.cpp\llama-server.exe" }
$server = Get-Command $serverCommand -ErrorAction SilentlyContinue
if (!$server) { throw "No se puede verificar el ejecutable de los modelos locales." }
$modelPaths = @(
    $(if ($env:SONG_AI_GEMMA_GGUF_PATH) { $env:SONG_AI_GEMMA_GGUF_PATH } else { Join-Path $Root "data\models\llm\gemma\gemma.gguf" }),
    $(if ($env:SONG_AI_QWEN_GGUF_PATH) { $env:SONG_AI_QWEN_GGUF_PATH } else { Join-Path $Root "data\models\llm\qwen\qwen.gguf" })
)
function Test-ModelPortOpen([string]$Url, [int]$DefaultPort) {
    $port = $DefaultPort
    try { $port = ([Uri]$Url).Port } catch { }
    if ($port -le 0) { $port = $DefaultPort }
    $client = New-Object Net.Sockets.TcpClient
    try {
        $connect = $client.BeginConnect('127.0.0.1', $port, $null, $null)
        if (!$connect.AsyncWaitHandle.WaitOne(250)) { return $false }
        $client.EndConnect($connect)
        return $true
    } catch { return $false }
    finally { $client.Close() }
}
# PID ausentes o antiguos no impiden encontrar los servidores del proyecto.
# Verificar ejecutable y modelo; nunca cerrar otros servidores llama.cpp.
$expectedName = [IO.Path]::GetFileName($server.Source).Replace("'", "''")
$cimUnavailable = $false
try {
    $candidates = @(Get-CimInstance Win32_Process -Filter "Name = '$expectedName'")
} catch {
    $cimUnavailable = $true
    $candidates = @()
}
$ownedServers = @($candidates | Where-Object {
    $candidate = $_
    $candidate.ExecutablePath -eq $server.Source -and @($modelPaths | Where-Object {
        $candidate.CommandLine -and $candidate.CommandLine.IndexOf($_, [StringComparison]::OrdinalIgnoreCase) -ge 0
    }).Count -gt 0
})
if ($cimUnavailable) {
    # A managed shell may deny CIM. Trust only PID records written at process start,
    # with the exact project executable and a matching creation time.
    $pidFiles = @(Get-ChildItem -LiteralPath $RuntimeDir -Filter "*.pid" -ErrorAction SilentlyContinue |
        Where-Object { $_.BaseName -in @('gemma', 'qwen') })
    if (!$pidFiles.Count) {
        $gemmaUrl = if ($env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL) { $env:SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL } else { 'http://localhost:8081' }
        $qwenUrl = if ($env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL) { $env:SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL } else { 'http://localhost:8082' }
        if ((Test-ModelPortOpen $gemmaUrl 8081) -or (Test-ModelPortOpen $qwenUrl 8082)) {
            throw "CIM no disponible y hay un servidor de modelos sin PID verificado; no iniciar audio."
        }
        Write-Host '[LLM] CIM denegado, sin PID gestionados y puertos de modelos cerrados.'
    }
    foreach ($pidFile in $pidFiles) {
        $pidValue = Get-Content -LiteralPath $pidFile.FullName -ErrorAction Stop | Select-Object -First 1
        $parsedPid = 0
        if (![int]::TryParse($pidValue, [ref]$parsedPid) -or $parsedPid -le 0) {
            throw "PID invalido para $($pidFile.BaseName); no iniciar audio."
        }
        $process = Get-Process -Id $parsedPid -ErrorAction SilentlyContinue
        if ($null -eq $process) {
            Remove-Item -LiteralPath $pidFile.FullName -Force
            continue
        }
        $seconds = [math]::Abs(($pidFile.LastWriteTime - $process.StartTime).TotalSeconds)
        if ($process.Path -ne $server.Source -or $process.Name -ne [IO.Path]::GetFileNameWithoutExtension($server.Source) -or $seconds -gt 120) {
            throw "PID $parsedPid no corresponde al servidor administrado; no iniciar audio."
        }
        $ownedServers += [pscustomobject]@{ ProcessId = $parsedPid }
    }
}
foreach ($owned in $ownedServers) {
    Write-Host "[LLM] Deteniendo servidor verificado pid=$($owned.ProcessId)"
    Stop-Process -Id $owned.ProcessId -Force
    $remaining = Get-Process -Id $owned.ProcessId -ErrorAction SilentlyContinue
    if ($remaining) { $remaining.WaitForExit(10000) | Out-Null }
    if (Get-Process -Id $owned.ProcessId -ErrorAction SilentlyContinue) {
        throw "El servidor sigue activo. No iniciar audio."
    }
}

if (Test-Path -LiteralPath $RuntimeDir) { Get-ChildItem -LiteralPath $RuntimeDir -Filter "*.pid" | ForEach-Object {
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
    Write-Host "[LLM] PID $processId ajeno a los modelos verificados; se conserva."
} }
Write-Host "[LLM] Cierre de los modelos del proyecto verificado."
