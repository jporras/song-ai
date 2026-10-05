param(
    [ValidateSet("vulkan", "sycl")]
    [string]$Backend = "vulkan",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$InstallRoot = Join-Path $Root "data\tools\llama.cpp"
$Downloads = Join-Path $Root "data\downloads"
$EnvFile = Join-Path $Root ".env"
New-Item -ItemType Directory -Force -Path $InstallRoot, $Downloads | Out-Null

function Set-EnvLine([string]$Path, [string]$Name, [string]$Value) {
    $line = "$Name=$Value"
    if (!(Test-Path $Path)) {
        Set-Content -Path $Path -Value "$line`n" -Encoding utf8
        return
    }
    $content = Get-Content -Path $Path -Raw
    if ($content -match "(?m)^$([regex]::Escape($Name))=") {
        $content = [regex]::Replace($content, "(?m)^$([regex]::Escape($Name))=.*$", [System.Text.RegularExpressions.MatchEvaluator]{ param($m) $line })
        Set-Content -Path $Path -Value $content -Encoding utf8
    } else {
        Add-Content -Path $Path -Value $line -Encoding utf8
    }
}

function Find-Asset($release, [string]$BackendName) {
    $patterns = if ($BackendName -eq "vulkan") {
        @("bin-win-vulkan-x64.zip", "win-vulkan-x64.zip")
    } else {
        @("bin-win-sycl-x64.zip", "win-sycl-x64.zip")
    }
    foreach ($pattern in $patterns) {
        $asset = $release.assets | Where-Object { $_.name.ToLowerInvariant().Contains($pattern) } | Select-Object -First 1
        if ($asset) { return $asset }
    }
    return $null
}

$serverPath = Join-Path $InstallRoot "llama-server.exe"
if ((Test-Path $serverPath) -and !$Force) {
    Write-Host "[llama.cpp] Ya existe $serverPath. Usa -Force para reinstalar."
} else {
    Write-Host "[llama.cpp] Consultando release oficial de ggml-org/llama.cpp..."
    $headers = @{ "User-Agent" = "song-ai-local-installer" }
    $releases = Invoke-RestMethod -Uri "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=12" -Headers $headers
    $selectedAsset = $null
    $selectedRelease = $null
    foreach ($release in $releases) {
        $selectedAsset = Find-Asset $release $Backend
        if ($selectedAsset) {
            $selectedRelease = $release
            break
        }
    }
    if (!$selectedAsset) {
        throw "No encontre un asset Windows x64 para backend '$Backend'. Prueba -Backend vulkan o revisa https://github.com/ggml-org/llama.cpp/releases."
    }

    $zipPath = Join-Path $Downloads $selectedAsset.name
    Write-Host "[llama.cpp] Descargando $($selectedAsset.name) desde $($selectedRelease.tag_name)..."
    Invoke-WebRequest -Uri $selectedAsset.browser_download_url -OutFile $zipPath -Headers $headers

    $extractDir = Join-Path $Downloads ("llama-" + $selectedRelease.tag_name + "-" + $Backend)
    if (Test-Path $extractDir) { Remove-Item -LiteralPath $extractDir -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $extractDir | Out-Null
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force

    $foundServer = Get-ChildItem -Path $extractDir -Recurse -Filter "llama-server.exe" | Select-Object -First 1
    if (!$foundServer) {
        throw "El zip descargado no contiene llama-server.exe."
    }

    Get-ChildItem -Path $InstallRoot -Force | Remove-Item -Recurse -Force
    Copy-Item -Path (Join-Path $foundServer.Directory.FullName "*") -Destination $InstallRoot -Recurse -Force
}

Set-EnvLine -Path $EnvFile -Name "SONG_AI_LLAMA_SERVER_COMMAND" -Value $serverPath
Set-EnvLine -Path $EnvFile -Name "SONG_AI_LLAMA_CPP_INTERPRETER_BASE_URL" -Value "http://localhost:8081"
Set-EnvLine -Path $EnvFile -Name "SONG_AI_LLAMA_CPP_TECHNICAL_BASE_URL" -Value "http://localhost:8082"
Set-EnvLine -Path $EnvFile -Name "SONG_AI_LLAMA_CPP_CTX_SIZE" -Value "4096"
Set-EnvLine -Path $EnvFile -Name "SONG_AI_LLAMA_CPP_GPU_ARGS" -Value "--n-gpu-layers 999"
Set-EnvLine -Path $EnvFile -Name "SONG_AI_LLM_AUTOSTART" -Value "true"
Set-EnvLine -Path $EnvFile -Name "SONG_AI_STOP_LLM_ON_EXIT" -Value "true"

Write-Host "[llama.cpp] Configuracion lista."
Write-Host "[llama.cpp] Backend solicitado: $Backend"
Write-Host "[llama.cpp] Ejecutable: $serverPath"
Write-Host "[llama.cpp] Reinicia Song AI con: scripts\run-local.ps1 -Port 8000"
