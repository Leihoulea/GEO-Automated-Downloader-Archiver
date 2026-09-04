# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0-rc2] - 2026-09-04

### Fixed
- **SSH timeout and stdin DEVNULL** (from b0c14b86): `run_ssh` now sets
  `stdin=subprocess.DEVNULL` when no input is provided, preventing SSH from
  blocking on an unusable Session-0 stdin handle in S4U scheduled tasks.
  Added `command_timeout` parameter; connection check uses
  `max(30, connect_timeout + 10)` so the "true" probe cannot hang forever.
- **Bounded upload retry** (from fc58f258): individual file uploads now
  retry up to 4 times (max 10) with exponential backoff (base 5s, 2^n).
  `is_retryable_upload_error` distinguishes transient failures (retry)
  from permanent failures (skip). Failure audit log written to
  `auto_upload_failure_history.jsonl` with fsync for durability.
  Added `--upload-max-attempts` and `--upload-retry-base-seconds` CLI args.
- **Download completion reconciliation** (from a7e70177 concept):
  `download_launcher_status` now checks `download_summary.json` for terminal
  completion signals before checking for failure. If all files downloaded,
  0 corrupt, 0 missing, and no active .part files, status is set to
  COMPLETE with `reconciliation_source=download_summary_json`.

## [0.1.0-rc1] - 2026-09-04

### Added
- Standalone repository initialized with `.gitignore`, `README.md`, `pyproject.toml`
- Version audit report (`docs/version-audit-2026-08.md`) covering 17 commits from
  2026-08-20 to 2026-08-26, including blob SHA comparison and dependency closure
- Legacy source import record (`docs/legacy-source-import-record.md`) with blob SHA
  manifest for all 17 imported files
- Example configuration (`config/config.example.toml`, `.env.example`) covering
  batch root, download disk, SSH target, server archive, EUMETSAT credentials,
  concurrency, email SMTP, and network policy
- Unified launch scripts (`scripts/start_dashboard.ps1`, `scripts/start_batch.ps1`)
  with Python version check, dependency check, and hidden background launch
- `pyproject.toml` declaring `boto3`, `requests`, `psutil` dependencies

### Changed
- Imported 2026-08-20 downloader baseline from source commit `e02c2776`
- `paths.py`: removed hardcoded `D:\AAAresearch_paper`, `E:\GEO_Cloud_2024`, `F:\`
  defaults; replaced with repository-relative defaults + environment variable overrides
- `geo_ring_cloud_path_configuration.ps1`: same path defaults updated
- `geo_ring_cloud_transfer_batch.ps1`: fixed path config reference from sibling
  `geo_ring_cloud_stage1/` directory to same directory
- `CORE_CODE_ROOT` in 5 Python files updated from `parents[1] / "geo_ring_cloud_stage1"`
  to `parent` to match new package layout

### Fixed
- **Windows PID probing** (from f08ea0cd): `process_is_running` no longer calls
  `os.kill(pid, 0)` on Windows, which was killing the target process via
  `TerminateProcess`. Now uses `psutil.pid_exists` directly. This was the root
  cause of upload processes dying when the dashboard refreshed status.
- **Git subprocess console windows** (new fix): `lineage.py` subprocess calls to
  `git` now use `CREATE_NO_WINDOW` and `STARTUPINFO` with `SW_HIDE` on Windows,
  eliminating the black console window flashing on every status file write.
- **Detached download child activity** (new fix): `download_launcher_status` now
  checks for recent `.part` file activity even when the launcher status is `FAIL`,
  not just `STARTING`/`RUNNING`. This prevents false `FAIL` reports when the
  PowerShell parent exits but the Python downloader child is still active.
- **Windows background process launch** (from 0ebd1e8d concept): PS1 launcher now
  accepts `-PythonExe` parameter to invoke the Python interpreter directly instead
  of through `conda run`, avoiding wrapper process timing issues. Dashboard passes
  `sys.executable` automatically.
- **Path configuration relative path**: fixed `$GeoRingProjectRoot` from `..\..\..`
  to `..\..` to match the new `src/geo_downloader/` directory structure.

### Tags
- `legacy-2026.08.20` — historical functional baseline (e02c2776 import)
- `v1.0.0-rc1` — first release candidate with Windows fixes

### Known Issues
- Dashboard process management via PowerShell→conda run→Python chain is fragile
  on Windows. Recommended mode: run download and upload directly from command line
  or batch scripts; use dashboard for status display only.
- `AdaptiveS3RangeController` from b0ce5c1b is excluded (user-confirmed download
  bug). The baseline fixed 4 MiB Range request size is used instead.
- FY4B upload may fail if a remote file exists with different size than the local
  manifest expects. This is by design (refuses overwrite); the conflicting file
  must be resolved manually.
- Post-baseline P0/P1 fixes (SSH timeout, upload retry, startup recovery, etc.)
  are not yet ported. See `docs/version-audit-2026-08.md` section 6.2 for the
  full list.

### Test Results
- 56 baseline unit tests pass
- Download verified: 2025-03-01 to 2025-03-05 Himawari-9, 240 files, 12 workers
- Upload verified: continuous upload via SFTP to server, SHA-256 computed
- Dashboard verified: status display, task list, download/upload progress
