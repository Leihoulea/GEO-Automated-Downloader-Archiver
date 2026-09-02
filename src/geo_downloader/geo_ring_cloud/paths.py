"""Central path defaults and environment overrides.

All paths default to sensible values relative to this package, but every
path can be overridden through environment variables.  In production,
set GEO_RING_EXTERNAL_GEO_CLOUD_ROOT and GEO_RING_BATCH_ROOT at minimum.
"""

from __future__ import annotations

import os
from pathlib import Path


COMPONENT_ROLE = "path_configuration"

_PACKAGE_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _PACKAGE_ROOT.parents[2]


def env_path(name: str, default: str | Path) -> Path:
    return Path(os.environ.get(name, str(default)))


PROJECT_ROOT = env_path("GEO_RING_PROJECT_ROOT", _REPO_ROOT)
CODE_ROOT = env_path("GEO_RING_CODE_ROOT", _PACKAGE_ROOT)
EUMETSAT_CREDENTIALS_FILE = env_path(
    "GEO_RING_EUMETSAT_CREDENTIALS_FILE",
    _REPO_ROOT / "config" / "eumetsat_credentials.txt",
)

STAGE_ROOT = env_path("GEO_RING_STAGE_ROOT", _REPO_ROOT / "stage")
BASE_STAGE_ROOT = env_path("GEO_RING_BASE_STAGE_ROOT", STAGE_ROOT)
RUNS_ROOT = env_path("GEO_RING_RUNS_ROOT", _REPO_ROOT / "runs")
EVIDENCE_ROOT = env_path("GEO_RING_EVIDENCE_ROOT", _REPO_ROOT / "evidence")

DATA_CHECK_ROOT = env_path("GEO_RING_DATA_CHECK_ROOT", _REPO_ROOT / "data_check")
DATA_CHECK_GEOMETRY_ROOT = env_path(
    "GEO_RING_DATA_CHECK_GEOMETRY_ROOT",
    DATA_CHECK_ROOT / "geometry_variable_audit",
)
GEOMETRY_ROOT = env_path("GEO_RING_GEOMETRY_ROOT", _REPO_ROOT / "geometry")
DATA_ROOT = env_path("GEO_RING_DATA_ROOT", _REPO_ROOT / "data")
HIMAWARI_R21_DIR = env_path("GEO_RING_HIMAWARI_R21_DIR", DATA_ROOT / "H09_Data")

EXTERNAL_GEO_CLOUD_ROOT = env_path(
    "GEO_RING_EXTERNAL_GEO_CLOUD_ROOT",
    _REPO_ROOT / "data" / "GEO_Cloud_2024",
)
CLAAS3_ROOT = env_path("GEO_RING_CLAAS3_ROOT", EXTERNAL_GEO_CLOUD_ROOT / "CMSAF")
EXTERNAL_EPIC_L2_ROOT = env_path(
    "GEO_RING_EXTERNAL_EPIC_L2_ROOT",
    EXTERNAL_GEO_CLOUD_ROOT / "DSCOVR_EPIC_L2_CLOUD_03_2024.03",
)
EXTERNAL_EPIC_COMPOSITE_ROOT = env_path(
    "GEO_RING_EXTERNAL_EPIC_COMPOSITE_ROOT",
    EXTERNAL_GEO_CLOUD_ROOT / "DSCOVR_EPIC_L2_COMPOSITE_02_2024.01",
)

THIRD_REPORT_ROOT = env_path("GEO_RING_THIRD_REPORT_ROOT", _REPO_ROOT / "third_report")

__all__ = [
    "BASE_STAGE_ROOT",
    "CLAAS3_ROOT",
    "CODE_ROOT",
    "DATA_CHECK_GEOMETRY_ROOT",
    "DATA_CHECK_ROOT",
    "DATA_ROOT",
    "EVIDENCE_ROOT",
    "EUMETSAT_CREDENTIALS_FILE",
    "EXTERNAL_EPIC_L2_ROOT",
    "EXTERNAL_EPIC_COMPOSITE_ROOT",
    "EXTERNAL_GEO_CLOUD_ROOT",
    "GEOMETRY_ROOT",
    "HIMAWARI_R21_DIR",
    "PROJECT_ROOT",
    "RUNS_ROOT",
    "STAGE_ROOT",
    "THIRD_REPORT_ROOT",
    "env_path",
]
