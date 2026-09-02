# GEO Automated Downloader & Archiver - Batch Download Launcher
#
# This script starts a single download batch.  It does NOT start uploads
# or connect to cloud services without explicit user action.

param(
    [Parameter(Mandatory = $true)]
    [string]$BatchRoot,
    [Parameter(Mandatory = $true)]
    [string]$ServerRoot,
    [string]$StartDate = "2024-04-01",
    [string]$EndDate = "2024-04-01",
    [string]$Platforms = "GOES-16,GOES-18",
    [int]$InventoryWorkers = 8,
    [int]$DownloadWorkers = 4,
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"

$ScriptRoot = $PSScriptRoot
$CodeRoot = Join-Path $ScriptRoot "..\src\geo_downloader"
$BatchScript = Join-Path $CodeRoot "geo_ring_cloud_transfer_batch.ps1"

if (-not (Test-Path -LiteralPath $BatchScript -PathType Leaf)) {
    throw "Batch script not found: $BatchScript"
}

$PathConfig = Join-Path $CodeRoot "geo_ring_cloud_path_configuration.ps1"
if (-not (Test-Path -LiteralPath $PathConfig -PathType Leaf)) {
    throw "Path configuration not found: $PathConfig"
}
. $PathConfig

$ResolvedPythonExe = if ($PythonExe) {
    [System.IO.Path]::GetFullPath($PythonExe)
} elseif ($env:GEO_RING_PYTHON_EXE) {
    $env:GEO_RING_PYTHON_EXE
} else {
    $GeoRingPythonExe
}

& $BatchScript `
    -BatchRoot $BatchRoot `
    -ServerRoot $ServerRoot `
    -StartDate $StartDate `
    -EndDate $EndDate `
    -Platforms $Platforms `
    -InventoryWorkers $InventoryWorkers `
    -DownloadWorkers $DownloadWorkers `
    -PythonExe $ResolvedPythonExe
