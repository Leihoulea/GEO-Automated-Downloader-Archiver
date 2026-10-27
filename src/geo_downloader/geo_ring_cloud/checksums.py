"""Durable SHA-256 cache shared by local prepare/upload processes.

The downloader and uploader can both hash the same immutable data files.  This
module stores ``(path, size, mtime_ns) -> sha256`` rows in a JSONL control file
and serializes cache misses with a cross-process file lock, so a resumed batch
does not re-read the entire dataset just to rebuild a manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple


CACHE_FILE_NAME = "checksum_cache.jsonl"
LOCK_FILE_NAME = "checksum.lock"
DEFAULT_CHUNK_SIZE = 8 * 1024 * 1024
LOCK_TIMEOUT_SECONDS = 3600.0


def sha256_file(path: Path, chunk_size: int = DEFAULT_CHUNK_SIZE) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


class _CrossProcessLock:
    """Exclusive lock on a single byte of a control file."""

    def __init__(self, path: Path, timeout_seconds: float = LOCK_TIMEOUT_SECONDS):
        self.path = Path(path)
        self.timeout_seconds = timeout_seconds
        self._handle = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a+b")
        self._handle.seek(0, os.SEEK_END)
        if self._handle.tell() == 0:
            self._handle.write(b"\0")
            self._handle.flush()
        deadline = time.monotonic() + max(1.0, self.timeout_seconds)
        if os.name == "nt":
            import msvcrt

            while True:
                try:
                    self._handle.seek(0)
                    msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
                    return self
                except OSError:
                    if time.monotonic() >= deadline:
                        self._handle.close()
                        self._handle = None
                        raise TimeoutError(
                            "timed out waiting for checksum lock: {}".format(self.path)
                        )
                    time.sleep(0.1)
        import fcntl

        fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._handle is None:
            return
        try:
            if os.name == "nt":
                import msvcrt

                self._handle.seek(0)
                msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        finally:
            self._handle.close()
            self._handle = None


class ChecksumCache:
    """Append-only JSONL cache of file checksums."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.lock_path = self.path.parent / LOCK_FILE_NAME
        self._lock = threading.Lock()
        self._entries: Dict[str, Tuple[int, int, str]] = {}
        self._offset = 0
        self._remainder = b""
        self.refresh()

    @staticmethod
    def _key(path: Path) -> str:
        return str(Path(path).resolve())

    def refresh(self) -> None:
        with self._lock:
            try:
                size = self.path.stat().st_size
            except OSError:
                return
            if size < self._offset:
                self._entries.clear()
                self._offset = 0
                self._remainder = b""
            try:
                with self.path.open("rb") as handle:
                    handle.seek(self._offset)
                    data = handle.read()
                    self._offset = handle.tell()
            except OSError:
                return
            if not data:
                return
            data = self._remainder + data
            lines = data.split(b"\n")
            self._remainder = lines.pop()
            for line in lines:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if not isinstance(row, dict):
                    continue
                local_path = str(row.get("local_path", "")).strip()
                sha256 = str(row.get("sha256", "")).strip()
                if not local_path or not sha256:
                    continue
                try:
                    size_bytes = int(row.get("size_bytes", -1))
                    mtime_ns = int(row.get("mtime_ns", -1))
                except (TypeError, ValueError):
                    continue
                if size_bytes < 0 or mtime_ns < 0:
                    continue
                self._entries[self._key(Path(local_path))] = (
                    size_bytes,
                    mtime_ns,
                    sha256,
                )

    def lookup(self, path: Path, size_bytes: int, mtime_ns: int) -> Optional[str]:
        with self._lock:
            entry = self._entries.get(self._key(path))
        if entry is None:
            return None
        if entry[0] != int(size_bytes) or entry[1] != int(mtime_ns):
            return None
        return entry[2]

    def _append(self, path: Path, size_bytes: int, mtime_ns: int, sha256: str) -> None:
        row = {
            "local_path": self._key(path),
            "size_bytes": int(size_bytes),
            "mtime_ns": int(mtime_ns),
            "sha256": sha256,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        serialized = json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(serialized)
            self._entries[self._key(path)] = (int(size_bytes), int(mtime_ns), sha256)

    def get_or_compute(self, path: Path) -> str:
        path = Path(path)
        for attempt in range(2):
            stat = path.stat()
            size_bytes = int(stat.st_size)
            mtime_ns = int(stat.st_mtime_ns)
            cached = self.lookup(path, size_bytes, mtime_ns)
            if cached is not None:
                return cached
            with _CrossProcessLock(self.lock_path):
                self.refresh()
                cached = self.lookup(path, size_bytes, mtime_ns)
                if cached is not None:
                    return cached
                digest = sha256_file(path)
                after = path.stat()
                if (
                    int(after.st_size) != size_bytes
                    or int(after.st_mtime_ns) != mtime_ns
                ):
                    if attempt == 0:
                        continue
                    raise RuntimeError(
                        "file changed while hashing: {}".format(path)
                    )
                self._append(path, size_bytes, mtime_ns, digest)
                return digest
        raise RuntimeError("file changed while hashing: {}".format(path))


def sha256_for_file(path: Path, cache: ChecksumCache) -> str:
    return cache.get_or_compute(path)
