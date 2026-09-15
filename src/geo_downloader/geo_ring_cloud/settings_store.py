"""Persistent, DPAPI-encrypted settings store for the dashboard.

All settings that a user would otherwise have to set via environment
variables or CLI flags are persisted here so the dashboard can run
"zero-config": the user fills in a web form once, and the values are
encrypted (secrets) or plain (non-secret paths) on disk.

Secrets (EUMETSAT key/secret, Earthdata password, SMTP password) are
protected with Windows DPAPI (user-scoped), exactly like the email
notification config in ``notifications.py``.

Non-secret settings (SSH target, identity-file path, server root,
download path, SMTP host/port) are stored in plain JSON so they can be
read back without a DPAPI round-trip.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .notifications import (
    _dpapi_protect,
    _dpapi_unprotect,
    utc_now_text,
    write_json_atomic,
)


COMPONENT_ROLE = "dashboard_settings"
SCHEMA_VERSION = 1

# Keys whose values are secrets and must be DPAPI-encrypted at rest.
SECRET_KEYS = (
    "eumetsat_consumer_key",
    "eumetsat_consumer_secret",
    "earthdata_password",
    "smtp_password",
)

# All known setting keys (used for validation / defaults).
KNOWN_KEYS = (
    "ssh_target",
    "identity_file",
    "server_root",
    "allowed_server_parent",
    "download_root",
    "conda_environment",
    "eumetsat_consumer_key",
    "eumetsat_consumer_secret",
    "earthdata_username",
    "earthdata_password",
    "smtp_host",
    "smtp_port",
    "smtp_user",
    "smtp_sender",
    "smtp_recipient",
    "smtp_ssl",
    "smtp_starttls",
    "smtp_password",
)

DEFAULTS: Dict[str, Any] = {
    "ssh_target": "",
    "identity_file": "",
    "server_root": "/data04/1/dhr/geo_ring_cloud_auto_upload",
    "allowed_server_parent": "/data04/1/dhr",
    "download_root": "",
    "conda_environment": "pytorch",
    "eumetsat_consumer_key": "",
    "eumetsat_consumer_secret": "",
    "earthdata_username": "",
    "earthdata_password": "",
    "smtp_host": "",
    "smtp_port": 465,
    "smtp_user": "",
    "smtp_sender": "",
    "smtp_recipient": "",
    "smtp_ssl": True,
    "smtp_starttls": False,
    "smtp_password": "",
}


def settings_path() -> Path:
    """Return the per-user dashboard settings file path."""
    configured = os.environ.get("GEO_RING_DASHBOARD_SETTINGS_PATH", "").strip()
    if configured:
        return Path(configured).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA", "").strip()
    if not local_app_data:
        return Path.home() / ".geo_ring_cloud" / "dashboard_settings.json"
    return Path(local_app_data) / "GeoRingCloud" / "dashboard_settings.json"


def save_settings(values: Dict[str, Any]) -> Path:
    """Persist settings, encrypting secrets with DPAPI."""
    path = settings_path()
    payload: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "component_role": COMPONENT_ROLE,
        "updated_at": utc_now_text(),
    }
    for key in KNOWN_KEYS:
        raw = values.get(key, DEFAULTS.get(key))
        if raw is None:
            raw = DEFAULTS.get(key, "")
        if key in SECRET_KEYS:
            text = str(raw or "")
            if text:
                payload[key + "_dpapi"] = _dpapi_protect(text)
                payload[key + "_scope"] = "WindowsCurrentUser"
            else:
                payload[key + "_dpapi"] = ""
                payload[key + "_scope"] = ""
        else:
            payload[key] = raw
    write_json_atomic(path, payload)
    return path


def load_settings() -> Dict[str, Any]:
    """Load and decrypt settings. Returns a flat dict with all keys in plain text."""
    path = settings_path()
    if not path.is_file():
        return dict(DEFAULTS)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return dict(DEFAULTS)
    except (OSError, json.JSONDecodeError):
        return dict(DEFAULTS)
    result: Dict[str, Any] = {}
    for key in KNOWN_KEYS:
        if key in SECRET_KEYS:
            encrypted = str(raw.get(key + "_dpapi", ""))
            if encrypted:
                try:
                    result[key] = _dpapi_unprotect(encrypted)
                except Exception:
                    result[key] = ""
            else:
                result[key] = ""
        else:
            result[key] = raw.get(key, DEFAULTS.get(key))
    return result


def public_settings() -> Dict[str, Any]:
    """Return settings with secrets masked, safe to send to the browser."""
    full = load_settings()
    public = dict(full)
    for key in SECRET_KEYS:
        val = public.get(key, "")
        public[key] = ("*" * 8) if val else ""
    public["settings_path"] = str(settings_path())
    public["has_eumetsat"] = bool(full.get("eumetsat_consumer_key") and full.get("eumetsat_consumer_secret"))
    public["has_earthdata"] = bool(full.get("earthdata_password"))
    public["has_smtp"] = bool(full.get("smtp_password"))
    public["has_ssh"] = bool(full.get("ssh_target") and full.get("identity_file"))
    return public


def apply_to_environment() -> None:
    """Load persisted settings into os.environ so downstream scripts see them.

    Called at dashboard startup.  Environment variables already set by the
    user take precedence (so power users can still override the file).
    """
    settings = load_settings()
    env_map = {
        "ssh_target": "GEO_RING_UPLOAD_SSH_TARGET",
        "identity_file": "GEO_RING_UPLOAD_IDENTITY_FILE",
        "server_root": "GEO_RING_AUTO_UPLOAD_ROOT",
        "allowed_server_parent": "GEO_RING_ALLOWED_SERVER_PARENT",
        "conda_environment": "GEO_RING_DOWNLOAD_CONDA_ENVIRONMENT",
        "download_root": "GEO_RING_EXTERNAL_GEO_CLOUD_ROOT",
        "eumetsat_consumer_key": "EUMETSAT_CONSUMER_KEY",
        "eumetsat_consumer_secret": "EUMETSAT_CONSUMER_SECRET",
        "earthdata_username": "EARTHDATA_USERNAME",
        "earthdata_password": "EARTHDATA_PASSWORD",
        "smtp_host": "GEO_RING_NOTIFY_SMTP_HOST",
        "smtp_user": "GEO_RING_NOTIFY_SMTP_USER",
        "smtp_password": "GEO_RING_NOTIFY_SMTP_PASSWORD",
        "smtp_sender": "GEO_RING_NOTIFY_EMAIL_FROM",
        "smtp_recipient": "GEO_RING_NOTIFY_EMAIL_TO",
    }
    for setting_key, env_key in env_map.items():
        value = settings.get(setting_key, "")
        if value and not os.environ.get(env_key):
            os.environ[env_key] = str(value)
    if settings.get("smtp_port") and not os.environ.get("GEO_RING_NOTIFY_SMTP_PORT"):
        os.environ["GEO_RING_NOTIFY_SMTP_PORT"] = str(settings["smtp_port"])
    if settings.get("smtp_ssl") is not None and not os.environ.get("GEO_RING_NOTIFY_SMTP_SSL"):
        os.environ["GEO_RING_NOTIFY_SMTP_SSL"] = "1" if settings.get("smtp_ssl") else "0"
    if settings.get("smtp_starttls") is not None and not os.environ.get("GEO_RING_NOTIFY_SMTP_STARTTLS"):
        os.environ["GEO_RING_NOTIFY_SMTP_STARTTLS"] = "1" if settings.get("smtp_starttls") else "0"


__all__ = [
    "apply_to_environment",
    "load_settings",
    "public_settings",
    "save_settings",
    "settings_path",
    "KNOWN_KEYS",
    "SECRET_KEYS",
    "DEFAULTS",
]
