"""Configuration management for Maestro.

Handles loading and saving user settings to a JSON file.
"""

import copy
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
    "transpose": False,
    "show_preview": False,
    "key_layout": "22-key (Full)",
    "wwm_key_layout": "36-key (Full)",
    "sharp_handling": "skip",
    "favorites": [],
    "recently_played": [],
    "play_key": "f2",
    "stop_key": "f3",
    "emergency_stop_key": "escape",
    "theme": "dark",
    "disclaimer_accepted": False,
    "start_fullscreen": False,
    "check_updates_on_launch": True,
    "auto_minimize_on_play": True,
    "countdown_delay": 3,
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


def validate_config(config: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Validate config values, reset invalid ones to defaults.

    Args:
        config: Config dict to validate

    Returns:
        Tuple of (validated config, list of warning messages)
    """
    warnings = []

    # Validate game_mode
    valid_game_modes = ["Heartopia", "Where Winds Meet", "Once Human"]
    if config.get("game_mode") not in valid_game_modes:
        warnings.append(f"Invalid game_mode '{config.get('game_mode')}', reset to default")
        config["game_mode"] = DEFAULT_CONFIG["game_mode"]

    # Validate speed (float, 0.5-2.0)
    speed = config.get("speed")
    if not isinstance(speed, (int, float)) or speed < 0.5 or speed > 2.0:
        warnings.append(f"Invalid speed '{speed}', reset to default")
        config["speed"] = DEFAULT_CONFIG["speed"]

    # Validate preview_lookahead (int, 2/5/10)
    if config.get("preview_lookahead") not in [2, 5, 10]:
        warnings.append(
            f"Invalid preview_lookahead '{config.get('preview_lookahead')}', reset to default"
        )
        config["preview_lookahead"] = DEFAULT_CONFIG["preview_lookahead"]

    # Validate booleans
    for key in [
        "transpose",
        "show_preview",
        "disclaimer_accepted",
        "start_fullscreen",
        "check_updates_on_launch",
        "auto_minimize_on_play",
    ]:
        if not isinstance(config.get(key), bool):
            warnings.append(f"Invalid {key} '{config.get(key)}', reset to default")
            config[key] = DEFAULT_CONFIG[key]

    # Validate countdown_delay (int, 0-10)
    countdown = config.get("countdown_delay")
    if not isinstance(countdown, int) or countdown < 0 or countdown > 10:
        warnings.append(f"Invalid countdown_delay '{countdown}', reset to default")
        config["countdown_delay"] = DEFAULT_CONFIG["countdown_delay"]

    # Validate theme
    if config.get("theme") not in ["dark", "light"]:
        warnings.append(f"Invalid theme '{config.get('theme')}', reset to default")
        config["theme"] = DEFAULT_CONFIG["theme"]

    # Validate key_layout
    valid_layouts = [
        "22-key (Full)",
        "15-key (Double Row)",
        "15-key (Triple Row)",
        "Conga/Cajon (8-key)",
        "Xylophone (8-key)",
    ]
    if config.get("key_layout") not in valid_layouts:
        warnings.append(f"Invalid key_layout '{config.get('key_layout')}', reset to default")
        config["key_layout"] = DEFAULT_CONFIG["key_layout"]

    # Validate wwm_key_layout
    valid_wwm_layouts = ["36-key (Full)", "21-key (Naturals)"]
    if config.get("wwm_key_layout") not in valid_wwm_layouts:
        warnings.append(
            f"Invalid wwm_key_layout '{config.get('wwm_key_layout')}', reset to default"
        )
        config["wwm_key_layout"] = DEFAULT_CONFIG["wwm_key_layout"]

    # Validate sharp_handling
    if config.get("sharp_handling") not in ["skip", "snap"]:
        warnings.append(
            f"Invalid sharp_handling '{config.get('sharp_handling')}', reset to default"
        )
        config["sharp_handling"] = DEFAULT_CONFIG["sharp_handling"]

    # Validate lists
    for key in ["favorites", "recently_played"]:
        if not isinstance(config.get(key), list):
            warnings.append(f"Invalid {key}, reset to default")
            config[key] = DEFAULT_CONFIG[key]

    # Validate hotkey strings
    for key in ["play_key", "stop_key", "emergency_stop_key"]:
        if not isinstance(config.get(key), str) or not config[key]:
            warnings.append(f"Invalid {key} '{config.get(key)}', reset to default")
            config[key] = DEFAULT_CONFIG[key]

    return config, warnings


def load_config() -> dict[str, Any]:
    """Load config from JSON file. Returns defaults for missing keys."""
    config_path = get_config_path()
    config = copy.deepcopy(DEFAULT_CONFIG)

    if config_path.exists():
        try:
            with open(config_path) as f:
                saved = json.load(f)
                config.update(saved)
        except (OSError, json.JSONDecodeError):
            pass

    config, warnings = validate_config(config)
    for warning in warnings:
        # Use print since logger may not be initialized yet
        print(f"Config warning: {warning}")

    return config


def save_config(settings: dict[str, Any]) -> None:
    """Save settings to JSON file.

    Swallows OSError (locked file, read-only FS, disk full) and serialization
    errors with a printed warning rather than crashing the app. load_config
    follows the same pattern.
    """
    try:
        config_dir = get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = get_config_path()
        with open(config_path, "w") as f:
            json.dump(settings, f, indent=2)
    except (OSError, TypeError, ValueError) as e:
        print(f"Failed to save config: {e}")
