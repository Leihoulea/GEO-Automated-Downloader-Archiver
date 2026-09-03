$COMPONENT_ROLE = "path_configuration"

$GeoRingProjectRoot = if ($env:GEO_RING_PROJECT_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_PROJECT_ROOT)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot "..\.."))
}

$GeoRingThirdReportRoot = if ($env:GEO_RING_THIRD_REPORT_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_THIRD_REPORT_ROOT)
} else {
    Join-Path $GeoRingProjectRoot "third_report"
}

$GeoRingCoreCodeRoot = if ($env:GEO_RING_CODE_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_CODE_ROOT)
} else {
    $PSScriptRoot
}

$GeoRingDataCheckRoot = if ($env:GEO_RING_DATA_CHECK_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_DATA_CHECK_ROOT)
} else {
    Join-Path $GeoRingProjectRoot "data_check"
}

$GeoRingRunsRoot = if ($env:GEO_RING_RUNS_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_RUNS_ROOT)
} else {
    Join-Path $GeoRingProjectRoot "runs"
}

$GeoRingExternalGeoCloudRoot = if ($env:GEO_RING_EXTERNAL_GEO_CLOUD_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_EXTERNAL_GEO_CLOUD_ROOT)
} else {
    Join-Path $GeoRingProjectRoot "data\GEO_Cloud_2024"
}

$GeoRingClaas3Root = if ($env:GEO_RING_CLAAS3_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_CLAAS3_ROOT)
} else {
    Join-Path $GeoRingExternalGeoCloudRoot "CMSAF"
}

$GeoRingExternalEpicL2Root = if ($env:GEO_RING_EXTERNAL_EPIC_L2_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_EXTERNAL_EPIC_L2_ROOT)
} else {
    Join-Path $GeoRingExternalGeoCloudRoot "DSCOVR_EPIC_L2_CLOUD_03_2024.03"
}

$GeoRingExternalEpicCompositeRoot = if ($env:GEO_RING_EXTERNAL_EPIC_COMPOSITE_ROOT) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_EXTERNAL_EPIC_COMPOSITE_ROOT)
} else {
    Join-Path $GeoRingExternalGeoCloudRoot "DSCOVR_EPIC_L2_COMPOSITE_02_2024.01"
}

$GeoRingEumetsatCredentialsFile = if ($env:GEO_RING_EUMETSAT_CREDENTIALS_FILE) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_EUMETSAT_CREDENTIALS_FILE)
} else {
    Join-Path $GeoRingProjectRoot "config\eumetsat_credentials.txt"
}

$GeoRingPythonExe = if ($env:GEO_RING_PYTHON_EXE) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_PYTHON_EXE)
} else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonCommand.Source } else { "python" }
}

$GeoRingCondaExe = if ($env:GEO_RING_CONDA_EXE) {
    [System.IO.Path]::GetFullPath($env:GEO_RING_CONDA_EXE)
} else {
    $condaCommand = Get-Command conda -ErrorAction SilentlyContinue
    if ($condaCommand) { $condaCommand.Source } else { "conda" }
}
