# Legacy Source Import Record

This file records the provenance of every file imported from the legacy
repository `D:\AAAresearch_paper` at commit `e02c2776` (2026-08-20).

## Source Metadata

- source_repository: D:\AAAresearch_paper
- source_commit: e02c277696ebb087a1e049f40d9213e23c0c22a1
- source_branch: codex/governance-recovery-20260812
- import_timestamp: 2026-09-02

## File Manifest

| Target path | Source path | Source blob SHA |
|-------------|-------------|-----------------|
| src/geo_downloader/__init__.py | (created) | - |
| src/geo_downloader/geo_ring_cloud_transfer_dashboard.py | third_report/code/geo_cloud_download/geo_ring_cloud_transfer_dashboard.py | a136ae8b1ff9ae9526aabbcd8c80bf4b1aeed999 |
| src/geo_downloader/geo_ring_cloud_auto_uploader.py | third_report/code/geo_cloud_download/geo_ring_cloud_auto_uploader.py | 628ef904c70ab835f4760467e6f4854f399f3a08 |
| src/geo_downloader/geo_cloud_downloader.py | third_report/code/geo_cloud_download/geo_cloud_downloader.py | 4c78c3d1bf2daf4e52dcf8d705b40743bb1cd1a0 |
| src/geo_downloader/geo_ring_cloud_transfer_batch.py | third_report/code/geo_cloud_download/geo_ring_cloud_transfer_batch.py | 46a48931daa50e6270af3e0b70ff1603cf7c44b7 |
| src/geo_downloader/geo_ring_cloud_transfer_batch.ps1 | third_report/code/geo_cloud_download/geo_ring_cloud_transfer_batch.ps1 | 4e8694c0b5bd6be6451d1314412796083d7f2cdb |
| src/geo_downloader/geo_ring_cloud_notification_service.py | third_report/code/geo_cloud_download/geo_ring_cloud_notification_service.py | 29d43ea8e876491fbce24f0df1955b8722e35f44 |
| src/geo_downloader/monitor_dashboard.py | third_report/code/geo_cloud_download/monitor_dashboard.py | 0ddb31d5b487bf64f5bd5bcbe6b9cfbb7e24b11d |
| src/geo_downloader/geo_ring_cloud_transfer_dashboard.html | third_report/code/geo_cloud_download/geo_ring_cloud_transfer_dashboard.html | 5180fdab9d57a7324b5b055313a8fa3e36a0844c |
| src/geo_downloader/geo_ring_cloud_data_transfer_operation_guide_cn.md | third_report/code/geo_cloud_download/geo_ring_cloud_data_transfer_operation_guide_cn.md | 462f89ac19aff42c9af1ccef37bcc43dae4f09ae |
| src/geo_downloader/geo_ring_cloud_path_configuration.ps1 | third_report/code/geo_ring_cloud_stage1/geo_ring_cloud_path_configuration.ps1 | d8582e641b204f95fb36200486ea5ca08cca3e3d |
| src/geo_downloader/tests/test_geo_ring_cloud_transfer_batch.py | third_report/code/geo_cloud_download/tests/test_geo_ring_cloud_transfer_batch.py | 623ff2ad9c7af362ba8ca913e3b9510d230f0368 |
| src/geo_downloader/geo_ring_cloud/__init__.py | third_report/code/geo_ring_cloud_stage1/geo_ring_cloud/__init__.py | 55c06b37730b88b326e79af27ea3d54b13c1cfc2 |
| src/geo_downloader/geo_ring_cloud/paths.py | third_report/code/geo_ring_cloud_stage1/geo_ring_cloud/paths.py | 86a2199f65725083058dfa56f8da564f606755d6 |
| src/geo_downloader/geo_ring_cloud/lineage.py | third_report/code/geo_ring_cloud_stage1/geo_ring_cloud/lineage.py | 428cc7c730afca767ae7ede5aefcb10ee01e1bb2 |
| src/geo_downloader/geo_ring_cloud/sources.py | third_report/code/geo_ring_cloud_stage1/geo_ring_cloud/sources.py | b7926f36bd45a44af2371d006d9c438ba0b9a514 |
| src/geo_downloader/geo_ring_cloud/batch_queue.py | third_report/code/geo_ring_cloud_stage1/geo_ring_cloud/batch_queue.py | 2544ca41988ea6dda5bc6ee374636b3cf416cd98 |
| src/geo_downloader/geo_ring_cloud/notifications.py | third_report/code/geo_ring_cloud_stage1/geo_ring_cloud/notifications.py | 8c427e97e394b8474edf39e6a8411070768c9d5a |

## Modifications Applied During Import

The only modification to imported files is the `CORE_CODE_ROOT` path in
five Python files. The original code used:

    CORE_CODE_ROOT = Path(__file__).resolve().parents[1] / "geo_ring_cloud_stage1"

This assumed the `geo_ring_cloud` package lived in a sibling directory
`geo_ring_cloud_stage1/`. In the standalone repository, the package is
moved into the same directory as the downloader scripts. The path was
changed to:

    CORE_CODE_ROOT = Path(__file__).resolve().parent

This is the only functional change. All other file contents are byte-for-byte
identical to the source commit.

## Test Results

    56 passed in 4.82s

All 56 baseline tests pass with the modified import paths.
