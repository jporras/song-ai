param([string]$ShortcutPath = '', [string]$ProjectRoot = '')

$ErrorActionPreference = 'Stop'
if (-not $ProjectRoot) { $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$Launcher = Join-Path $ProjectRoot 'scripts\open-song-ai.ps1'
if (-not (Test-Path -LiteralPath $Launcher)) { throw 'No se encontro scripts\open-song-ai.ps1.' }
if (-not $ShortcutPath) {
    $Desktop = [Environment]::GetFolderPath('DesktopDirectory')
    if (-not $Desktop) { throw 'No se pudo localizar el escritorio de Windows.' }
    $ShortcutPath = Join-Path $Desktop 'Song AI.lnk'
}
$ShortcutPath = [System.IO.Path]::GetFullPath($ShortcutPath)
if ([System.IO.Path]::GetExtension($ShortcutPath) -ne '.lnk') {
    throw 'El acceso directo debe terminar en .lnk.'
}
if (-not (Test-Path -LiteralPath (Split-Path -Parent $ShortcutPath))) {
    throw 'La carpeta de destino del acceso directo no existe.'
}
$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$Shortcut.Arguments = '-NoProfile -ExecutionPolicy Bypass -File "' + $Launcher + '"'
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = 'Abrir Song AI en el navegador'
$Shortcut.IconLocation = "$env:SystemRoot\System32\shell32.dll,14"
$Shortcut.Save()
Write-Host "Acceso directo creado: $ShortcutPath"
