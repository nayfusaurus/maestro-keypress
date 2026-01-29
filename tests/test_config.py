"""Tests for the config module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from maestro.config import (
    DEFAULT_CONFIG,
    get_config_dir,
    get_config_path,
    load_config,
    save_config,
)


class TestGetConfigDir:
    """Tests for get_config_dir function."""

    def test_get_config_dir_windows(self):
        """On Windows, config dir should be %APPDATA%/Maestro."""
        with patch("maestro.config.sys.platform", "win32"):
            with patch.dict("os.environ", {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
                config_dir = get_config_dir()
                assert config_dir == Path("C:\\Users\\Test\\AppData\\Roaming") / "Maestro"

    def test_get_config_dir_linux(self):
        """On Linux, config dir should be ~/.maestro."""
        with patch("maestro.config.sys.platform", "linux"):
            with patch("maestro.config.Path.home", return_value=Path("/home/testuser")):
                config_dir = get_config_dir()
                assert config_dir == Path("/home/testuser") / ".maestro"

    def test_get_config_dir_macos(self):
        """On macOS, config dir should be ~/.maestro."""
        with patch("maestro.config.sys.platform", "darwin"):
            with patch("maestro.config.Path.home", return_value=Path("/Users/testuser")):
                config_dir = get_config_dir()
                assert config_dir == Path("/Users/testuser") / ".maestro"


class TestGetConfigPath:
    """Tests for get_config_path function."""

    def test_get_config_path(self):
        """Config path should be config.json inside config dir."""
        with patch("maestro.config.get_config_dir", return_value=Path("/test/config")):
            config_path = get_config_path()
            assert config_path == Path("/test/config") / "config.json"


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_defaults(self, tmp_path):
        """Returns defaults when no config file exists."""
        with patch("maestro.config.get_config_path", return_value=tmp_path / "nonexistent.json"):
            config = load_config()
            assert config == DEFAULT_CONFIG

    def test_load_config_with_existing_file(self, tmp_path):
        """Loads settings from existing config file."""
        config_path = tmp_path / "config.json"
        saved_config = {"last_songs_folder": "/my/songs", "game_mode": "WhereWindsMeet"}
        config_path.write_text(json.dumps(saved_config))

        with patch("maestro.config.get_config_path", return_value=config_path):
            config = load_config()
            assert config["last_songs_folder"] == "/my/songs"
            assert config["game_mode"] == "WhereWindsMeet"
            # Defaults should be preserved for missing keys
            assert config["speed"] == DEFAULT_CONFIG["speed"]
            assert config["preview_lookahead"] == DEFAULT_CONFIG["preview_lookahead"]

    def test_load_config_with_invalid_json(self, tmp_path):
        """Returns defaults when config file contains invalid JSON."""
        config_path = tmp_path / "config.json"
        config_path.write_text("not valid json {{{")

        with patch("maestro.config.get_config_path", return_value=config_path):
            config = load_config()
            assert config == DEFAULT_CONFIG

    def test_load_config_preserves_extra_keys(self, tmp_path):
        """Config retains extra keys from file that aren't in defaults."""
        config_path = tmp_path / "config.json"
        saved_config = {"last_songs_folder": "/songs", "custom_setting": "value"}
        config_path.write_text(json.dumps(saved_config))

        with patch("maestro.config.get_config_path", return_value=config_path):
            config = load_config()
            assert config["custom_setting"] == "value"


class TestSaveConfig:
    """Tests for save_config function."""

    def test_save_config_creates_file(self, tmp_path):
        """Saves config to JSON file."""
        config_dir = tmp_path / "maestro"
        config_path = config_dir / "config.json"

        with patch("maestro.config.get_config_dir", return_value=config_dir):
            with patch("maestro.config.get_config_path", return_value=config_path):
                settings = {"last_songs_folder": "/my/songs", "speed": 1.5}
                save_config(settings)

                assert config_path.exists()
                loaded = json.loads(config_path.read_text())
                assert loaded["last_songs_folder"] == "/my/songs"
                assert loaded["speed"] == 1.5

    def test_save_config_creates_directory(self, tmp_path):
        """Creates config directory if it doesn't exist."""
        config_dir = tmp_path / "nested" / "maestro"
        config_path = config_dir / "config.json"

        with patch("maestro.config.get_config_dir", return_value=config_dir):
            with patch("maestro.config.get_config_path", return_value=config_path):
                save_config({"test": "value"})
                assert config_dir.exists()


class TestSaveAndLoadRoundtrip:
    """Tests for save/load roundtrip."""

    def test_save_and_load_config(self, tmp_path):
        """Config survives roundtrip save and load."""
        config_dir = tmp_path / "maestro"
        config_path = config_dir / "config.json"

        with patch("maestro.config.get_config_dir", return_value=config_dir):
            with patch("maestro.config.get_config_path", return_value=config_path):
                original = {
                    "last_songs_folder": "/path/to/songs",
                    "game_mode": "WhereWindsMeet",
                    "speed": 0.75,
                    "preview_lookahead": 10,
                }
                save_config(original)
                loaded = load_config()

                assert loaded["last_songs_folder"] == original["last_songs_folder"]
                assert loaded["game_mode"] == original["game_mode"]
                assert loaded["speed"] == original["speed"]
                assert loaded["preview_lookahead"] == original["preview_lookahead"]
