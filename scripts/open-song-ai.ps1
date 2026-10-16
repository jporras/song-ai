param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Runner = Join-Path $PSScriptRoot 'run-local.ps1'
$Python = Join-Path $ProjectRoot '.venv\Scripts\pythonw.exe'
$Frontend = Join-Path $ProjectRoot 'frontend\dist\index.html'
$Url = "http://127.0.0.1:$Port/"

if ($Port -lt 1 -or $Port -gt 65535) { throw 'El puerto debe estar entre 1 y 65535.' }
if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Song AI necesita preparacion inicial. Ejecuta scripts\setup-local.ps1.'
}
if (-not (Test-Path -LiteralPath $Frontend)) {
    throw 'Falta la interfaz compilada. Ejecuta npm run build dentro de frontend.'
}
$Listener = [System.Net.Sockets.TcpClient]::new()
try {
    $Listener.Connect('127.0.0.1', $Port)
    throw "El puerto $Port ya esta ocupado. Cierra la otra aplicacion o inicia Song AI con otro puerto."
} catch [System.Net.Sockets.SocketException] {
    # Puerto libre: el servidor puede iniciarse.
} finally {
    $Listener.Dispose()
}

Write-Host "Iniciando Song AI. Se abrira el navegador en $Url cuando este listo."
Write-Host 'Para cerrar Song AI, vuelve a esta ventana y pulsa Ctrl+C.'
$BrowserWaiter = Start-Process -FilePath $Python -ArgumentList @(
    ('"' + (Join-Path $PSScriptRoot 'open-browser-when-ready.py') + '"'), $Url
) -WorkingDirectory $ProjectRoot -PassThru -WindowStyle Hidden
try {
    & $Runner -Port $Port
    if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    $BrowserWaiter.Refresh()
    if (-not $BrowserWaiter.HasExited) {
        Stop-Process -Id $BrowserWaiter.Id -ErrorAction SilentlyContinue
    }
}
