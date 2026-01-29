"""Configuration management for Maestro.

Handles loading and saving user settings to a JSON file.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = {
    "last_songs_folder": "",
    "game_mode": "Heartopia",
    "speed": 1.0,
    "preview_lookahead": 5,
}


def get_config_dir() -> Path:
    """Return platform-appropriate config directory.

    Windows: %APPDATA%/Maestro
    Linux/Mac: ~/.maestro
    """
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        return Path(appdata) / "Maestro"
    else:
        return Path.home() / ".maestro"


def get_config_path() -> Path:
    """Return path to config file."""
    return get_config_dir() / "config.json"


def load_config() -> dict[str, Any]:
    """Load config from JSON file. Returns defaults for missing keys."""
    config_path = get_config_path()
    config = DEFAULT_CONFIG.copy()

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                saved = json.load(f)
                config.update(saved)
        except (json.JSONDecodeError, IOError):
            pass

    return config


def save_config(settings: dict[str, Any]) -> None:
    """Save settings to JSON file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(settings, f, indent=2)
