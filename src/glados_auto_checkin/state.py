from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class LockError(Exception):
    """Raised when another process already owns the lock."""


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        logging.warning("State file is unreadable, ignoring it: %s", path)
        return {}


def write_state(path: Path, state: dict[str, Any]) -> None:
    ensure_parent(path)
    temp_path = path.with_suffix(".tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp_path.replace(path)


@dataclass
class FileLock:
    path: Path
    fd: int

    def release(self) -> None:
        try:
            os.close(self.fd)
        finally:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass


def acquire_lock(lock_path: Path, stale_seconds: int) -> FileLock:
    ensure_parent(lock_path)
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if not lock_path.exists():
                continue
            try:
                payload = json.loads(lock_path.read_text(encoding="utf-8"))
            except Exception:
                payload = {}
            created_at = float(payload.get("created_at", 0))
            if created_at and (time.time() - created_at) > stale_seconds:
                try:
                    lock_path.unlink()
                    continue
                except FileNotFoundError:
                    continue
            raise LockError(f"Another check-in process is already running (lock: {lock_path})")
        else:
            payload = {
                "pid": os.getpid(),
                "created_at": time.time(),
            }
            os.write(fd, json.dumps(payload).encode("utf-8"))
            os.fsync(fd)
            return FileLock(path=lock_path, fd=fd)
