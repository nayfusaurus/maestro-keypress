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
    validate_config,
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
        saved_config = {"last_songs_folder": "/my/songs", "game_mode": "Where Winds Meet"}
        config_path.write_text(json.dumps(saved_config))

        with patch("maestro.config.get_config_path", return_value=config_path):
            config = load_config()
            assert config["last_songs_folder"] == "/my/songs"
            assert config["game_mode"] == "Where Winds Meet"
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
                    "game_mode": "Where Winds Meet",
                    "speed": 0.75,
                    "preview_lookahead": 10,
                }
                save_config(original)
                loaded = load_config()

                assert loaded["last_songs_folder"] == original["last_songs_folder"]
                assert loaded["game_mode"] == original["game_mode"]
                assert loaded["speed"] == original["speed"]
                assert loaded["preview_lookahead"] == original["preview_lookahead"]


class TestNewSettings:
    """Tests for new transpose and show_preview settings."""

    def test_default_transpose_is_false(self):
        """Default config should have transpose=False."""
        assert DEFAULT_CONFIG["transpose"] is False

    def test_default_show_preview_is_false(self):
        """Default config should have show_preview=False."""
        assert DEFAULT_CONFIG["show_preview"] is False

    def test_load_config_includes_new_defaults(self, tmp_path):
        """Loading config without new keys should get default values."""
        config_path = tmp_path / "config.json"
        # Old config without new keys
        old_config = {"last_songs_folder": "/songs", "speed": 1.0}
        config_path.write_text(json.dumps(old_config))

        with patch("maestro.config.get_config_path", return_value=config_path):
            config = load_config()
            assert config["transpose"] is False
            assert config["show_preview"] is False

    def test_save_and_load_new_settings(self, tmp_path):
        """New settings survive roundtrip save and load."""
        config_dir = tmp_path / "maestro"
        config_path = config_dir / "config.json"

        with patch("maestro.config.get_config_dir", return_value=config_dir):
            with patch("maestro.config.get_config_path", return_value=config_path):
                original = {
                    "transpose": True,
                    "show_preview": True,
                }
                save_config(original)
                loaded = load_config()

                assert loaded["transpose"] is True
                assert loaded["show_preview"] is True

    def test_default_key_layout(self):
        """Default config should have key_layout='22-key (Full)'."""
        assert DEFAULT_CONFIG["key_layout"] == "22-key (Full)"

    def test_default_sharp_handling(self):
        """Default config should have sharp_handling='skip'."""
        assert DEFAULT_CONFIG["sharp_handling"] == "skip"

    def test_default_favorites(self):
        """Default config should have empty favorites list."""
        assert DEFAULT_CONFIG["favorites"] == []

    def test_default_recently_played(self):
        """Default config should have empty recently_played list."""
        assert DEFAULT_CONFIG["recently_played"] == []

    def test_default_play_key(self):
        """Default config should have play_key='f2'."""
        assert DEFAULT_CONFIG["play_key"] == "f2"

    def test_default_stop_key(self):
        """Default config should have stop_key='f3'."""
        assert DEFAULT_CONFIG["stop_key"] == "f3"

    def test_default_emergency_stop_key(self):
        """Default config should have emergency_stop_key='escape'."""
        assert DEFAULT_CONFIG["emergency_stop_key"] == "escape"


class TestValidateConfig:
    """Tests for validate_config function."""

    def test_valid_config_passes_unchanged(self):
        """A fully valid config should pass through without changes or warnings."""
        config = DEFAULT_CONFIG.copy()
        # Use list copies so we don't share references
        config["favorites"] = []
        config["recently_played"] = []
        validated, warnings = validate_config(config)
        assert warnings == []
        assert validated == config

    def test_invalid_game_mode_gets_reset(self):
        """Invalid game_mode should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["game_mode"] = "InvalidGame"
        validated, warnings = validate_config(config)
        assert validated["game_mode"] == "Heartopia"
        assert len(warnings) == 1
        assert "game_mode" in warnings[0]

    def test_invalid_speed_too_low(self):
        """Speed below 0.25 should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["speed"] = 0.1
        validated, warnings = validate_config(config)
        assert validated["speed"] == 1.0
        assert any("speed" in w for w in warnings)

    def test_invalid_speed_too_high(self):
        """Speed above 1.5 should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["speed"] = 2.0
        validated, warnings = validate_config(config)
        assert validated["speed"] == 1.0
        assert any("speed" in w for w in warnings)

    def test_invalid_speed_wrong_type(self):
        """Non-numeric speed should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["speed"] = "fast"
        validated, warnings = validate_config(config)
        assert validated["speed"] == 1.0
        assert any("speed" in w for w in warnings)

    def test_invalid_preview_lookahead(self):
        """Invalid preview_lookahead should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["preview_lookahead"] = 7
        validated, warnings = validate_config(config)
        assert validated["preview_lookahead"] == 5
        assert any("preview_lookahead" in w for w in warnings)

    def test_invalid_booleans(self):
        """Non-boolean transpose/show_preview should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["transpose"] = "yes"
        config["show_preview"] = 1
        validated, warnings = validate_config(config)
        assert validated["transpose"] is False
        assert validated["show_preview"] is False
        assert any("transpose" in w for w in warnings)
        assert any("show_preview" in w for w in warnings)

    def test_invalid_key_layout(self):
        """Invalid key_layout should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["key_layout"] = "99-key (Mega)"
        validated, warnings = validate_config(config)
        assert validated["key_layout"] == "22-key (Full)"
        assert any("key_layout" in w for w in warnings)

    def test_valid_drums_layout(self):
        """Conga/Cajon (8-key) should be recognized as valid key_layout."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["key_layout"] = "Conga/Cajon (8-key)"
        validated, warnings = validate_config(config)
        assert validated["key_layout"] == "Conga/Cajon (8-key)"
        assert len(warnings) == 0

    def test_invalid_sharp_handling(self):
        """Invalid sharp_handling should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["sharp_handling"] = "ignore"
        validated, warnings = validate_config(config)
        assert validated["sharp_handling"] == "skip"
        assert any("sharp_handling" in w for w in warnings)

    def test_invalid_lists(self):
        """Non-list favorites/recently_played should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = "not a list"
        config["recently_played"] = 42
        validated, warnings = validate_config(config)
        assert validated["favorites"] == []
        assert validated["recently_played"] == []
        assert any("favorites" in w for w in warnings)
        assert any("recently_played" in w for w in warnings)

    def test_invalid_hotkey_strings(self):
        """Non-string or empty hotkey values should be reset to default."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["play_key"] = 123
        config["stop_key"] = ""
        config["emergency_stop_key"] = None
        validated, warnings = validate_config(config)
        assert validated["play_key"] == "f2"
        assert validated["stop_key"] == "f3"
        assert validated["emergency_stop_key"] == "escape"
        assert any("play_key" in w for w in warnings)
        assert any("stop_key" in w for w in warnings)
        assert any("emergency_stop_key" in w for w in warnings)

    def test_multiple_invalid_values_produce_multiple_warnings(self):
        """Multiple invalid values should produce multiple warnings."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        config["game_mode"] = "Bad"
        config["speed"] = -1
        config["key_layout"] = "Bad"
        validated, warnings = validate_config(config)
        assert len(warnings) == 3

    def test_validate_config_returns_warnings_list(self):
        """validate_config should always return a list as second element."""
        config = DEFAULT_CONFIG.copy()
        config["favorites"] = []
        config["recently_played"] = []
        _, warnings = validate_config(config)
        assert isinstance(warnings, list)
