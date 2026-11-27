# SPDX-License-Identifier: MPL-2.0
"""Logging configuration for Maestro.

Sets up rotating file handler for error logging.
"""

import hashlib
import logging
import os
import re
import stat
import subprocess  # nosec B404
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from maestro.config import get_config_dir

_logger: logging.Logger | None = None


def get_log_path() -> Path:
    """Keep each downloaded executable's rotating logs separate across launches."""
    if getattr(sys, "frozen", False):
        executable = Path(sys.executable)
        stat = executable.stat()
        # Windows preserves the creation time on launch and the file ID on rename.
        identity = (
            stat.st_dev,
            stat.st_ino,
            getattr(stat, "st_birthtime_ns", 0),
            stat.st_size,
            stat.st_mtime_ns,
        )
        key = hashlib.sha256(str(identity).encode("ascii")).hexdigest()[:24]
        return get_config_dir() / "logs" / key / "maestro.log"
    return get_config_dir() / "maestro.log"


def _log_directories() -> list[Path]:
    root = get_config_dir() / "logs"
    if not root.exists() or _linked(root):
        return []
    return [
        p
        for p in root.iterdir()
        if re.fullmatch(r"[0-9a-f]{24}", p.name) and not _linked(p) and p.is_dir()
    ]


def _linked(path: Path) -> bool:
    info = path.lstat()
    return stat.S_ISLNK(info.st_mode) or bool(
        getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    )


def _clear_directory(directory: Path, active: Path, remove_directory: bool) -> None:
    for name in ("maestro.log", "maestro.log.1", "maestro.log.2", "maestro.log.3"):
        path = directory / name
        if not path.exists() or _linked(path) or not path.is_file():
            continue
        if path == active:
            path.write_bytes(b"")
        else:
            path.unlink()
    if remove_directory and not any(directory.iterdir()):
        directory.rmdir()


def clear_all_logs() -> None:
    """Remove Maestro log history while keeping the active writer usable."""
    active = get_log_path()
    for directory in _log_directories():
        _clear_directory(directory, active, directory != active.parent)
    _clear_directory(get_config_dir(), active, False)


def _prune_old_logs(active: Path) -> None:
    previous = sorted(
        (d for d in _log_directories() if d != active.parent),
        key=lambda d: d.stat().st_mtime_ns,
        reverse=True,
    )
    for directory in previous[2:]:
        _clear_directory(directory, active, True)


def setup_logger() -> logging.Logger:
    """Set up and return the maestro logger.

    Creates rotating file handler (1MB max, 3 backups).

    Returns:
        Configured logger instance
    """
    global _logger
    if _logger is not None:
        return _logger

    _logger = logging.getLogger("maestro")
    _logger.setLevel(logging.DEBUG)

    # Ensure log directory exists
    log_path = get_log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    if getattr(sys, "frozen", False):
        try:
            _prune_old_logs(log_path)
        except OSError as error:
            _logger.warning("Could not prune previous log files: %s", error)

    # Rotating file handler: 1MB max, keep 3 backups
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    _logger.addHandler(handler)

    return _logger


def open_log_file() -> None:
    """Open log file in default text editor."""
    log_path = get_log_path()
    if not log_path.exists():
        return

    if sys.platform == "win32":
        os.startfile(log_path)  # nosec B606
    elif sys.platform == "darwin":
        subprocess.run(["open", str(log_path)])  # nosec B603 B607
    else:
        subprocess.run(["xdg-open", str(log_path)])  # nosec B603 B607
