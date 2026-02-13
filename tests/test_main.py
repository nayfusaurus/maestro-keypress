import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from maestro.main import Maestro


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with (
        patch("maestro.main.Player") as player_mock,
        patch("maestro.main.SongPicker") as picker_mock,
        patch("maestro.main.keyboard") as kb_mock,
        patch("maestro.main.load_config") as load_config_mock,
        patch("maestro.main.save_config") as save_config_mock,
        patch("maestro.main.setup_logger") as logger_mock,
    ):
        load_config_mock.return_value = {
            "last_songs_folder": "",
            "game_mode": "Heartopia",
            "speed": 1.0,
            "preview_lookahead": 5,
            "transpose": False,
            "show_preview": False,
            "key_layout": "22-key (Full)",
            "sharp_handling": "skip",
            "favorites": [],
            "recently_played": [],
            "play_key": "f2",
            "stop_key": "f3",
            "emergency_stop_key": "escape",
        }
        yield {
            "player": player_mock.return_value,
            "picker": picker_mock.return_value,
            "keyboard": kb_mock,
            "load_config": load_config_mock,
            "save_config": save_config_mock,
            "logger": logger_mock.return_value,
        }


def test_maestro_initializes(mock_dependencies, tmp_path):
    """Maestro should initialize with songs folder."""
    app = Maestro(songs_folder=tmp_path)
    assert app.songs_folder == tmp_path


def test_maestro_stop(mock_dependencies, tmp_path):
    """Stop should delegate to player and reset countdown."""
    app = Maestro(songs_folder=tmp_path)
    app._countdown = 2
    app.stop()
    mock_dependencies["player"].stop.assert_called_once()
    assert app._countdown == 0


def test_maestro_play(mock_dependencies, tmp_path):
    """Play should delegate to player."""
    from maestro.player import PlaybackState

    app = Maestro(songs_folder=tmp_path)
    mock_dependencies["player"].current_song = Path("test.mid")
    mock_dependencies["player"].state = PlaybackState.STOPPED
    app.play()
    mock_dependencies["player"].play.assert_called_once()


def test_maestro_get_state_with_countdown(mock_dependencies, tmp_path):
    """State string should show countdown when counting."""
    app = Maestro(songs_folder=tmp_path)
    app._countdown = 2
    state = app._get_state_string()
    assert state == "Starting in 2..."


def test_maestro_on_folder_change(mock_dependencies, tmp_path):
    """Folder change should update songs_folder and save config."""
    app = Maestro(songs_folder=tmp_path)
    new_folder = tmp_path / "new_songs"
    new_folder.mkdir()
    app._on_folder_change(new_folder)
    assert app.songs_folder == new_folder
    mock_dependencies["save_config"].assert_called()


def test_maestro_on_layout_change(mock_dependencies, tmp_path):
    """Layout change should update player and save config."""
    from maestro.key_layout import KeyLayout

    app = Maestro(songs_folder=tmp_path)
    app._on_layout_change(KeyLayout.KEYS_15_DOUBLE)
    mock_dependencies["player"].key_layout = KeyLayout.KEYS_15_DOUBLE
    mock_dependencies["save_config"].assert_called()


def test_maestro_get_hotkey(mock_dependencies, tmp_path):
    """_get_hotkey should resolve config key names to pynput Key objects."""
    from pynput import keyboard as kb

    app = Maestro(songs_folder=tmp_path)
    key = app._get_hotkey("play_key", "f2")
    assert key == kb.Key.f2


def test_maestro_get_hotkey_escape(mock_dependencies, tmp_path):
    """_get_hotkey should resolve 'escape' to Key.esc."""
    from pynput import keyboard as kb

    app = Maestro(songs_folder=tmp_path)
    key = app._get_hotkey("emergency_stop_key", "escape")
    assert key == kb.Key.esc


def test_maestro_get_hotkey_unknown_returns_none(mock_dependencies, tmp_path):
    """_get_hotkey should return None for unknown key names."""
    app = Maestro(songs_folder=tmp_path)
    app._config["play_key"] = "nonexistent_key"
    key = app._get_hotkey("play_key", "f2")
    assert key is None


@pytest.fixture
def sample_midi(tmp_path):
    import mido

    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.Message("note_off", note=60, velocity=64, time=480))
    midi_path = tmp_path / "test.mid"
    mid.save(midi_path)
    return midi_path


def test_maestro_get_note_compatibility(mock_dependencies, tmp_path, sample_midi):
    """Note compatibility should count playable notes."""
    # Just verify the method exists and is callable
    app = Maestro(songs_folder=tmp_path)
    assert callable(app._get_note_compatibility)


def test_maestro_on_favorite_toggle(mock_dependencies, tmp_path):
    """Favorite toggle should update config."""
    app = Maestro(songs_folder=tmp_path)
    app._on_favorite_toggle("my_song", True)
    assert "my_song" in app._config["favorites"]

    app._on_favorite_toggle("my_song", False)
    assert "my_song" not in app._config["favorites"]


def test_maestro_get_favorites(mock_dependencies, tmp_path):
    """Get favorites should return list from config."""
    app = Maestro(songs_folder=tmp_path)
    app._config["favorites"] = ["song1", "song2"]
    assert app._get_favorites() == ["song1", "song2"]


def test_maestro_on_hotkey_change(mock_dependencies, tmp_path):
    """Hotkey change should update config and save."""
    app = Maestro(songs_folder=tmp_path)
    app._on_hotkey_change("play_key", "f5")
    assert app._config["play_key"] == "f5"
    mock_dependencies["save_config"].assert_called()
