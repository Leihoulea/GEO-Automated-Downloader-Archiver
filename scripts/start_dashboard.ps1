# GEO Automated Downloader & Archiver - Dashboard Launcher
# component_role: data_transfer_dashboard_service
#
# This script checks prerequisites and starts the dashboard HTTP server in
# a hidden background window.  It does NOT start any downloads.

param(
    [Parameter(Mandatory = $true)]
    [string]$BatchRoot,
    [string]$Host_ = "127.0.0.1",
    [int]$Port = 8765,
    [string]$SshTarget = "",
    [string]$IdentityFile = "",
    [string]$AutoUploadRoot = "",
    [string]$AllowedServerParent = "",
    [string]$CondaEnvironment = "",
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

# --- Resolve paths ---
$ScriptRoot = $PSScriptRoot
$CodeRoot = Join-Path $ScriptRoot "..\src\geo_downloader"
$PathConfig = Join-Path $CodeRoot "geo_ring_cloud_path_configuration.ps1"
$DashboardScript = Join-Path $CodeRoot "geo_ring_cloud_transfer_dashboard.py"

if (-not (Test-Path -LiteralPath $PathConfig -PathType Leaf)) {
    throw "Path configuration not found: $PathConfig"
}
. $PathConfig

if (-not (Test-Path -LiteralPath $DashboardScript -PathType Leaf)) {
    throw "Dashboard script not found: $DashboardScript"
}

# --- Resolve Python executable ---
$ResolvedPythonExe = if ($PythonExe) {
    [System.IO.Path]::GetFullPath($PythonExe)
} elseif ($env:GEO_RING_PYTHON_EXE) {
    $env:GEO_RING_PYTHON_EXE
} else {
    $GeoRingPythonExe
}
if (-not (Test-Path -LiteralPath $ResolvedPythonExe -PathType Leaf)) {
    throw "Python executable not found: $ResolvedPythonExe. Set GEO_RING_PYTHON_EXE or pass -PythonExe."
}

# --- Check Python version ---
$VersionOutput = & $ResolvedPythonExe -c "import sys; print(f'{sys.version_info[0]}.{sys.version_info[1]}')" 2>&1
$PyVersion = $VersionOutput.ToString().Trim()
Write-Host "Python version: $PyVersion at $ResolvedPythonExe"

# --- Check required Python packages ---
$RequiredPackages = @("psutil")
foreach ($Pkg in $RequiredPackages) {
    $CheckResult = & $ResolvedPythonExe -c "import $Pkg" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Missing Python package: $Pkg. Install with: pip install $Pkg"
    }
}

# --- Check batch root ---
$BatchRootResolved = [System.IO.Path]::GetFullPath($BatchRoot)
if (-not (Test-Path -LiteralPath $BatchRootResolved -PathType Container)) {
    Write-Host "Creating batch root: $BatchRootResolved"
    New-Item -ItemType Directory -Path $BatchRootResolved -Force | Out-Null
}

# --- Build command ---
$CommandArgs = @(
    $DashboardScript,
    "--batch-root", $BatchRootResolved,
    "--host", $Host_,
    "--port", $Port
)
if ($SshTarget) { $CommandArgs += @("--ssh-target", $SshTarget) }
if ($IdentityFile) { $CommandArgs += @("--identity-file", $IdentityFile) }
if ($AutoUploadRoot) { $CommandArgs += @("--auto-upload-root", $AutoUploadRoot) }
if ($AllowedServerParent) { $CommandArgs += @("--allowed-server-parent", $AllowedServerParent) }
if ($CondaEnvironment) { $CommandArgs += @("--conda-environment", $CondaEnvironment) }

# --- Prepare log path ---
$TransferDir = Join-Path $BatchRootResolved "transfer"
New-Item -ItemType Directory -Path $TransferDir -Force | Out-Null
$ServiceLog = Join-Path $TransferDir "dashboard_service.log"

# --- Launch hidden background process ---
$CreationFlags = (
    [System.Diagnostics.Process]::CreateNoWindow -bor
    [System.Diagnostics.Process]::CREATE_NEW_PROCESS_GROUP
)

Write-Host "Starting dashboard at http://${Host_}:${Port}"
Write-Host "Batch root: $BatchRootResolved"
Write-Host "Log: $ServiceLog"
Write-Host "Press Ctrl+C to stop."

& $ResolvedPythonExe @CommandArgs *>> $ServiceLog
