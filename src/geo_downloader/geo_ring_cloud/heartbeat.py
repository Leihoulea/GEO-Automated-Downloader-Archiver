"""Heartbeat-based process liveness and batch state machine.

This module replaces PID probing with a heartbeat protocol: each running
process writes a small JSON file every HEARTBEAT_INTERVAL_SECONDS. The
dashboard reads the heartbeat to determine if the process is alive,
what phase it is in, and how much progress it has made.

State machine:
    PENDING -> DOWNLOADING -> DOWNLOADED -> UPLOADING -> UPLOADED -> VERIFIED -> DONE
                   |              |            |            |
                FAILED         FAILED       FAILED      FAILED

Terminal states (DONE, FAILED) are sticky: once reached, the heartbeat
is no longer refreshed and the dashboard relies on terminal artifacts
(download_summary.json, server_verification.json) for authoritative
status.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional


HEARTBEAT_INTERVAL_SECONDS = 10
HEARTBEAT_STALE_SECONDS = 45

DOWNLOAD_HEARTBEAT_NAME = "download_heartbeat.json"
UPLOAD_HEARTBEAT_NAME = "upload_heartbeat.json"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _epoch_now() -> float:
    return time.time()


def write_heartbeat(
    path: Path,
    *,
    pid: int,
    phase: str,
    completed: int = 0,
    total: int = 0,
    extra: Optional[Dict[str, object]] = None,
) -> None:
    """Write a heartbeat JSON file atomically.

    Called by the download/upload process every HEARTBEAT_INTERVAL_SECONDS.
    """
    payload: Dict[str, object] = {
        "pid": pid,
        "phase": phase,
        "completed": completed,
        "total": total,
        "timestamp_epoch": _epoch_now(),
        "timestamp_utc": _utc_now_iso(),
    }
    if extra:
        payload.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".{}.{}.tmp".format(path.name, os.getpid()))
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        os.replace(temporary, path)
    except OSError:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def read_heartbeat(path: Path) -> Dict[str, object]:
    """Read a heartbeat file and determine liveness.

    Returns a dict with keys:
        exists: bool
        alive: bool (heartbeat is fresh)
        stale: bool (heartbeat exists but is old)
        pid: int (from heartbeat)
        phase: str (from heartbeat)
        completed: int
        total: int
        age_seconds: float
    """
    if not path.is_file():
        return {
            "exists": False,
            "alive": False,
            "stale": False,
            "pid": 0,
            "phase": "",
            "completed": 0,
            "total": 0,
            "age_seconds": None,
        }
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {
            "exists": True,
            "alive": False,
            "stale": True,
            "pid": 0,
            "phase": "",
            "completed": 0,
            "total": 0,
            "age_seconds": None,
        }
    ts = float(payload.get("timestamp_epoch", 0) or 0)
    age = max(0.0, _epoch_now() - ts) if ts > 0 else None
    alive = age is not None and age < HEARTBEAT_STALE_SECONDS
    return {
        "exists": True,
        "alive": alive,
        "stale": not alive,
        "pid": int(payload.get("pid", 0) or 0),
        "phase": str(payload.get("phase", "")),
        "completed": int(payload.get("completed", 0) or 0),
        "total": int(payload.get("total", 0) or 0),
        "age_seconds": age,
    }


def should_heartbeat(last_write_monotonic: float) -> bool:
    """Check if enough time has passed for the next heartbeat.

    Uses time.monotonic() for interval measurement (not wall clock)
    to avoid issues with system clock adjustments.
    """
    return (time.monotonic() - last_write_monotonic) >= HEARTBEAT_INTERVAL_SECONDS


__all__ = [
    "HEARTBEAT_INTERVAL_SECONDS",
    "HEARTBEAT_STALE_SECONDS",
    "DOWNLOAD_HEARTBEAT_NAME",
    "UPLOAD_HEARTBEAT_NAME",
    "write_heartbeat",
    "read_heartbeat",
    "should_heartbeat",
]
