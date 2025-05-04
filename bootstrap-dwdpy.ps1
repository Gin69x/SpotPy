$dirName = "spotpy"
$baseDir = Join-Path $PWD $dirName
$batPath = Join-Path $baseDir "dwdpy.bat"
$pyScriptUrl = "https://raw.githubusercontent.com/Gin69x/SpotiDwd/main/spotpy.py"
$configUrl = "https://raw.githubusercontent.com/Gin69x/SpotiDwd/d12bae87c72811079d6afe05d994a5f01dcdd375/config.json"

# Create directory
New-Item -ItemType Directory -Path $baseDir -Force | Out-Null

# Download Python script
Invoke-WebRequest -Uri $pyScriptUrl -OutFile (Join-Path $baseDir "spotpy.py")

# Download config.json
Invoke-WebRequest -Uri $configUrl -OutFile (Join-Path $baseDir "config.json")

# Create dwdpy.bat with correct path
$batContent = "@echo off`npython `"$baseDir\spotpy.py`" %*"
Set-Content -Path $batPath -Value $batContent -Encoding ASCII

# Add directory to PATH (current user)
$envPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if (-not $envPath.Split(";") -contains $baseDir) {
    [System.Environment]::SetEnvironmentVariable("Path", "$envPath;$baseDir", "User")
    Write-Output "Added $baseDir to user PATH."
} else {
    Write-Output "Directory already in PATH."
}

# Open the directory
Start-Process "explorer.exe" $baseDir
