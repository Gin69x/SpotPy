<#
.SYNOPSIS
  Bootstraps dwdpy by downloading the Python script, template config, and creating a .bat launcher.

.DESCRIPTION
  Creates a `cmd` folder next to this script, downloads `spotidwd.py` and `config.json` into it,
  writes `dwdpy.bat` using %~dp0 to locate the Python script, and adds the folder to your user PATH.

.PARAMETER InstallSubdir
  Name of the subdirectory to install into (defaults to "cmd").

.PARAMETER ScriptUrl
  URL to download the main Python script from.

.PARAMETER ConfigUrl
  URL to download the template config.json from.
#>

param(
  [string]$InstallSubdir = 'cmd',
  [string]$ScriptUrl      = 'https://raw.githubusercontent.com/<your-user>/<your-repo>/main/spotidwd.py',
  [string]$ConfigUrl      = 'https://raw.githubusercontent.com/<your-user>/<your-repo>/main/config.json'
)

# 1) Determine install directory
$installDir = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) $InstallSubdir
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir | Out-Null
    Write-Host "✅ Created install directory: $installDir"
} else {
    Write-Host "ℹ️  Using existing directory: $installDir"
}

# 2) Download spotidwd.py
$scriptPath = Join-Path $installDir 'spotidwd.py'
try {
    Invoke-WebRequest -Uri $ScriptUrl -UseBasicParsing -OutFile $scriptPath -ErrorAction Stop
    Write-Host "✅ Downloaded Python script to $scriptPath"
}
catch {
    Write-Host "[red]✖ Failed to download spotidwd.py from $ScriptUrl[/red]"
    Write-Host $_.Exception.Message
    exit 1
}

# 3) Download config.json
$configPath = Join-Path $installDir 'config.json'
try {
    Invoke-WebRequest -Uri $ConfigUrl -UseBasicParsing -OutFile $configPath -ErrorAction Stop
    Write-Host "✅ Downloaded config template to $configPath"
}
catch {
    Write-Host "[yellow]⚠ Could not download config.json; you may need to create it manually.[/yellow]"
}

# 4) Write the dwdpy.bat launcher
$batPath = Join-Path $installDir 'dwdpy.bat'
$batContent = @'
@echo off
REM dwdpy launcher – forwards all args to the Python script in the same folder
python "%~dp0spotidwd.py" %*
'@
Set-Content -Path $batPath -Value $batContent -Encoding ASCII
Write-Host "✅ Created launcher batch file: $batPath"

# 5) Add installDir to USER PATH if needed
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if ($userPath.Split(';') -contains $installDir) {
    Write-Host "ℹ️  $installDir is already in your user PATH."
} else {
    $newPath = "$userPath;$installDir"
    [Environment]::SetEnvironmentVariable('Path',$newPath,'User')
    Write-Host "✅ Added $installDir to your user PATH."
}

Write-Host "`n🎉 Bootstrap complete! Please restart your terminal session to pick up the new PATH."
