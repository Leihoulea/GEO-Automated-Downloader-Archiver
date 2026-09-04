<# 
 .SYNOPSIS
   GEO Automated Downloader & Archiver - Unified Launcher
 .DESCRIPTION
   Starts the dashboard (read-only status display), a download process,
   and optionally a continuous upload process. All processes run in
   hidden background windows and are independent of the dashboard.
 .PARAMETER Mode
   dashboard-only: start only the dashboard
   download: start download + dashboard
   download-upload: start download + continuous upload + dashboard
   upload-only: start continuous upload only (for existing completed downloads)
 .PARAMETER BatchRoot
   The download root directory (e.g. F:\GEO_Cloud_2024)
 .PARAMETER BatchParent
   The batch parent directory for status files (e.g. F:\GEO_Cloud_2024_batches)
 .PARAMETER StartDate
   Download start date (YYYY-MM-DD)
 .PARAMETER EndDate
   Download end date (YYYY-MM-DD)
 .PARAMETER Platforms
   Comma-separated platform list (e.g. "Himawari-9" or "GOES-16,GOES-18")
 .PARAMETER MaxWorkers
   Download worker count (default: 12)
 .PARAMETER SshTarget
   SSH target for upload (e.g. dhr@210.45.127.28)
 .PARAMETER IdentityFile
   SSH private key path
 .PARAMETER ServerRoot
   Server upload root directory
 .PARAMETER AllowedServerParent
   Allowed server parent directory
 .EXAMPLE
   .\scripts\start_all.ps1 -Mode download-upload -BatchRoot F:\GEO_Cloud_2024 -BatchParent F:\GEO_Cloud_2024_batches -StartDate 2025-03-01 -EndDate 2025-03-05 -Platforms "Himawari-9" -MaxWorkers 12 -SshTarget dhr@210.45.127.28 -IdentityFile C:\Users\Administrator\.ssh\id_ed25519_node05_automation -ServerRoot /data04/1/dhr/geo_ring_cloud_auto_upload -AllowedServerParent /data04/1/dhr
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("dashboard-only","download","download-upload","upload-only")]
    [string]$Mode,
    [string]$BatchRoot = "F:\GEO_Cloud_2024",
    [string]$BatchParent = "F:\GEO_Cloud_2024_batches",
    [string]$StartDate = "",
    [string]$EndDate = "",
    [string]$Platforms = "Himawari-9",
    [int]$MaxWorkers = 12,
    [string]$SshTarget = "dhr@210.45.127.28",
    [string]$IdentityFile = "",
    [string]$ServerRoot = "/data04/1/dhr/geo_ring_cloud_auto_upload",
    [string]$AllowedServerParent = "/data04/1/dhr"
)

$ErrorActionPreference = "Stop"

# --- Resolve paths ---
$ScriptRoot = $PSScriptRoot
$CodeRoot = Join-Path $ScriptRoot "..\src\geo_downloader"
$PyExe = "D:\anaconda\envs\pytorch\python.exe"

if (-not (Test-Path $PyExe)) {
    $PyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $PyExe) { throw "Python not found" }
}

$DashboardScript = Join-Path $CodeRoot "geo_ring_cloud_transfer_dashboard.py"
$DownloaderScript = Join-Path $CodeRoot "geo_cloud_downloader.py"
$UploaderScript = Join-Path $CodeRoot "geo_ring_cloud_auto_uploader.py"

if (-not $IdentityFile) {
    $IdentityFile = Join-Path $env:USERPROFILE ".ssh\id_ed25519_node05_automation"
}

# --- Clear proxy env vars ---
$env:NO_PROXY = "*"
$env:no_proxy = "*"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""
$env:http_proxy = ""
$env:https_proxy = ""
$env:all_proxy = ""
$env:GEO_RING_EXTERNAL_GEO_CLOUD_ROOT = $BatchRoot

# --- Create batch parent if needed ---
if (-not (Test-Path $BatchParent)) { New-Item -ItemType Directory -Path $BatchParent -Force | Out-Null }

# --- Generate batch name ---
$BatchName = ""
if ($StartDate -and $EndDate) {
    $PlatformsShort = ($Platforms.Split(",") | ForEach-Object { $_.Trim().Substring(0,2).ToLower() }) -join "-"
    $S = $StartDate -replace "-",""
    $E = $EndDate -replace "-",""
    $BatchName = "${S}_${E}_$PlatformsShort"
}

# --- Start Dashboard ---
Write-Host "Starting dashboard at http://127.0.0.1:8765 ..."
$CurrentBatch = Join-Path $BatchParent "current_batch"
if (-not (Test-Path $CurrentBatch)) { New-Item -ItemType Directory -Path $CurrentBatch -Force | Out-Null }
Start-Process -FilePath $PyExe -ArgumentList @(
    $DashboardScript,
    "--batch-root", $CurrentBatch,
    "--host", "127.0.0.1", "--port", "8765",
    "--ssh-target", $SshTarget,
    "--identity-file", $IdentityFile,
    "--auto-upload-root", $ServerRoot,
    "--allowed-server-parent", $AllowedServerParent,
    "--conda-environment", "pytorch"
) -WindowStyle Hidden
Write-Host "  Dashboard started."

# --- Start Download ---
if ($Mode -in @("download","download-upload") -and $StartDate -and $EndDate) {
    Write-Host "Starting download: $StartDate to $EndDate, $Platforms, $MaxWorkers workers ..."
    $LogDir = Join-Path $BatchRoot "logs"
    if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir -Force | Out-Null }
    $DlLog = Join-Path $LogDir "download_s3_range.log"
    
    $PlatformArgs = ($Platforms.Split(",") | ForEach-Object { @("--platform", $_.Trim()) }) | ForEach-Object { $_ }
    $Args = @($DownloaderScript, "--root", $BatchRoot, "download-s3-range",
              "--start-date", $StartDate, "--end-date", $EndDate,
              "--max-workers", $MaxWorkers.ToString()) + $PlatformArgs
    
    Start-Process -FilePath $PyExe -ArgumentList $Args -RedirectStandardOutput $DlLog -WindowStyle Hidden
    Write-Host "  Download started. Log: $DlLog"
}

# --- Start Upload ---
if ($Mode -in @("download-upload","upload-only")) {
    Write-Host "Starting continuous upload ..."
    $BatchDir = Join-Path $BatchParent $BatchName
    if ($BatchName -and (Test-Path $BatchDir)) {
        $TransferDir = Join-Path $BatchDir "transfer"
    } else {
        $TransferDir = Join-Path $BatchRoot "transfer"
    }
    if (-not (Test-Path $TransferDir)) { New-Item -ItemType Directory -Path $TransferDir -Force | Out-Null }
    
    $StatusPath = Join-Path $TransferDir "auto_upload_status.json"
    $ReportPath = Join-Path $TransferDir "server_verification.json"
    $UploadLog = Join-Path $TransferDir "continuous_upload.log"
    
    $PlatformArgs = ($Platforms.Split(",") | ForEach-Object { @("--platform", $_.Trim()) }) | ForEach-Object { $_ }
    $Args = @($UploaderScript,
              "--watch-batch-root", $BatchRoot,
              "--target", $SshTarget,
              "--identity-file", $IdentityFile,
              "--server-root", $ServerRoot,
              "--allowed-server-parent", $AllowedServerParent,
              "--status", $StatusPath,
              "--verification-report", $ReportPath)
    
    if ($StartDate -and $EndDate) {
        $Args += @("--start-date", $StartDate, "--end-date", $EndDate)
    }
    $Args += $PlatformArgs
    $Args += @("--poll-seconds", "10", "--connect-timeout", "20", "--max-upload-workers", "4")
    
    Start-Process -FilePath $PyExe -ArgumentList $Args -RedirectStandardOutput $UploadLog -WindowStyle Hidden
    Write-Host "  Upload started. Log: $UploadLog"
}

Write-Host ""
Write-Host "Done. Dashboard: http://127.0.0.1:8765"
Write-Host "Note: Download and upload run independently of the dashboard."
Write-Host "      To stop them, use Task Manager or 'Stop-Process -Id <PID>'."
