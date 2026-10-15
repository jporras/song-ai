function Import-SongAiEnvironment([string]$EnvironmentFile) {
    if (!(Test-Path -LiteralPath $EnvironmentFile)) { return }
    foreach ($rawLine in Get-Content -LiteralPath $EnvironmentFile -Encoding UTF8) {
        $line = $rawLine.Trim()
        if (!$line -or $line.StartsWith('#') -or !$line.Contains('=')) { continue }
        $parts = $line.Split('=', 2)
        $key = $parts[0].Trim()
        if ($key -notmatch '^SONG_AI_[A-Z0-9_]+$') { continue }
        # Explicit process environment takes precedence, including empty values.
        if ($null -ne [Environment]::GetEnvironmentVariable($key, 'Process')) { continue }
        $value = $parts[1].Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($key, $value, 'Process')
    }
}
