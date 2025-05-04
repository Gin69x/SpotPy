$dirName = "spotpy"
$baseDir = Join-Path $PWD $dirName
$batPath = Join-Path $baseDir "spotpy.bat"
$pyScriptUrl = "https://raw.githubusercontent.com/Gin69x/SpotiDwd/main/spotpy.py"
$configUrl = "https://raw.githubusercontent.com/Gin69x/SpotiDwd/d12bae87c72811079d6afe05d994a5f01dcdd375/config.json"

# Create directory
New-Item -ItemType Directory -Path $baseDir -Force | Out-Null

# Download Python script
Invoke-WebRequest -Uri $pyScriptUrl -OutFile (Join-Path $baseDir "spotpy.py")

# Download config.json
Invoke-WebRequest -Uri $configUrl -OutFile (Join-Path $baseDir "config.json")

# Create spotpy.bat with the correct full path
$batContent = "@echo off`npython `"$baseDir\spotpy.py`" %*"
Set-Content -Path $batPath -Value $batContent -Encoding ASCII

# Normalize baseDir path (handle slash direction)
$normalizedBaseDir = $baseDir.TrimEnd('\') -replace '/', '\'

# Get current PATH as list and normalize entries
$envPathRaw = [Environment]::GetEnvironmentVariable("Path", "User")
$envPathList = $envPathRaw.Split(";") | ForEach-Object { ($_ -replace '/', '\').TrimEnd('\') }

# Debugging: Output current PATH
Write-Output "Current PATH:"
$envPathList | ForEach-Object { Write-Output $_ }

# Add to PATH if not already there
if (-not ($envPathList -contains $normalizedBaseDir)) {
    # Add new path to the user's PATH environment variable
    $newPath = "$envPathRaw;$normalizedBaseDir"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Output "✅ Added $baseDir to user PATH."
} else {
    Write-Output "ℹ️ Directory $baseDir is already in PATH."
}

# Verify if the directory was added by checking PATH again
$updatedEnvPathRaw = [Environment]::GetEnvironmentVariable("Path", "User")
$updatedEnvPathList = $updatedEnvPathRaw.Split(";") | ForEach-Object { ($_ -replace '/', '\').TrimEnd('\') }

# Debugging: Output updated PATH
Write-Output "Updated PATH after modification:"
$updatedEnvPathList | ForEach-Object { Write-Output $_ }

# Open the directory in File Explorer
Start-Process "explorer.exe" $baseDir
