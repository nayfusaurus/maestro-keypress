"""Logging configuration for Maestro.

Sets up rotating file handler for error logging.
"""

import logging
import os
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from maestro.config import get_config_dir


_logger: logging.Logger | None = None


def get_log_path() -> Path:
    """Return path to log file."""
    return get_config_dir() / "maestro.log"


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

    # Rotating file handler: 1MB max, keep 3 backups
    handler = RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=3,
    )
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
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
        os.startfile(log_path)
    elif sys.platform == "darwin":
        subprocess.run(["open", str(log_path)])
    else:
        subprocess.run(["xdg-open", str(log_path)])
