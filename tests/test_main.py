"""Tests for the main Maestro coordinator."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from maestro.main import Maestro


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with (
        patch("maestro.main.Player") as player_mock,
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
        yield {
            "player": player_mock.return_value,
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
    """Play should delegate to _on_play when a song is selected in the GUI."""
    from unittest.mock import MagicMock

    from maestro.player import PlaybackState

    app = Maestro(songs_folder=tmp_path)
    mock_dependencies["player"].state = PlaybackState.STOPPED

    # Simulate a window with a selected song
    song_path = Path("test.mid")
    mock_window = MagicMock()
    mock_window._dashboard._song_list.get_selected_song.return_value = song_path
    app.window = mock_window

    app.play()
    mock_dependencies["player"].load.assert_called_once_with(song_path)


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
    app._on_layout_change(KeyLayout.KEYS_15_DOUBLE.value)
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


def test_maestro_on_favorite_toggle(mock_dependencies, tmp_path):
    """Favorite toggle should update config."""
    app = Maestro(songs_folder=tmp_path)
    app._on_favorite_toggle("my_song", True)
    assert "my_song" in app._config["favorites"]

    app._on_favorite_toggle("my_song", False)
    assert "my_song" not in app._config["favorites"]


def test_maestro_on_wwm_layout_change(mock_dependencies, tmp_path):
    """WWM layout change should update player and save config."""
    from maestro.key_layout import WwmLayout

    app = Maestro(songs_folder=tmp_path)
    app._on_wwm_layout_change(WwmLayout.KEYS_21.value)
    assert app._config["wwm_key_layout"] == "21-key (Naturals)"
    mock_dependencies["save_config"].assert_called()


def test_maestro_on_hotkey_change(mock_dependencies, tmp_path):
    """Hotkey change should update config and save."""
    app = Maestro(songs_folder=tmp_path)
    app._on_hotkey_change("play_key", "f5")
    assert app._config["play_key"] == "f5"
    mock_dependencies["save_config"].assert_called()


def test_maestro_on_countdown_delay_change(mock_dependencies, tmp_path):
    """Countdown delay change should update config and save."""
    app = Maestro(songs_folder=tmp_path)
    app._on_countdown_delay_change(5)
    assert app._config["countdown_delay"] == 5
    mock_dependencies["save_config"].assert_called()


def test_play_during_countdown_is_noop(mock_dependencies, tmp_path):
    """Play hotkey during countdown must not reload song or restart timer."""
    from unittest.mock import MagicMock

    from maestro.player import PlaybackState

    app = Maestro(songs_folder=tmp_path)
    mock_dependencies["player"].state = PlaybackState.STOPPED

    song_path = Path("test.mid")
    mock_window = MagicMock()
    mock_window._dashboard._song_list.get_selected_song.return_value = song_path
    app.window = mock_window

    # First play — starts countdown.
    app.play()
    assert app._countdown > 0
    first_timer = app._countdown_timer
    assert first_timer is not None
    assert mock_dependencies["player"].load.call_count == 1

    # Second play while countdown is still running — should be a no-op:
    # same timer instance, same load count.
    app.play()
    assert mock_dependencies["player"].load.call_count == 1
    assert app._countdown_timer is first_timer


def test_stop_during_countdown_cancels_timer(mock_dependencies, tmp_path):
    """Stop hotkey during countdown must cancel it and clear the timer."""
    from unittest.mock import MagicMock

    from maestro.player import PlaybackState

    app = Maestro(songs_folder=tmp_path)
    mock_dependencies["player"].state = PlaybackState.STOPPED

    song_path = Path("test.mid")
    mock_window = MagicMock()
    mock_window._dashboard._song_list.get_selected_song.return_value = song_path
    app.window = mock_window

    app.play()
    assert app._countdown > 0
    assert app._countdown_timer is not None

    app.stop()
    assert app._countdown == 0
    assert app._countdown_timer is None
    mock_dependencies["player"].stop.assert_called()


def test_on_play_blocks_during_countdown(mock_dependencies, tmp_path):
    """GUI play-click path (_on_play) must also ignore requests mid-countdown."""
    from maestro.player import PlaybackState

    app = Maestro(songs_folder=tmp_path)
    mock_dependencies["player"].state = PlaybackState.STOPPED

    song_path = Path("test.mid")
    # First call starts the countdown.
    app._on_play(song_path)
    assert app._countdown > 0
    first_timer = app._countdown_timer
    assert mock_dependencies["player"].load.call_count == 1

    # Direct _on_play call (simulating the GUI button via play_requested signal)
    # must be a no-op while countdown is active.
    app._on_play(song_path)
    assert mock_dependencies["player"].load.call_count == 1
    assert app._countdown_timer is first_timer


def test_on_play_blocks_during_active_playback(mock_dependencies, tmp_path):
    """_on_play must ignore requests while the player is already playing."""
    from maestro.player import PlaybackState

    app = Maestro(songs_folder=tmp_path)
    mock_dependencies["player"].state = PlaybackState.PLAYING

    app._on_play(Path("test.mid"))
    mock_dependencies["player"].load.assert_not_called()
    assert app._countdown == 0


def test_exit_stops_workers_and_joins_listener(mock_dependencies, tmp_path):
    """_exit must stop window workers and join the pynput listener thread."""
    from unittest.mock import MagicMock, patch

    app = Maestro(songs_folder=tmp_path)
    app.window = MagicMock()
    listener = MagicMock()
    app._listener = listener

    with patch("PySide6.QtWidgets.QApplication.quit"):
        app._exit()

    app.window.stop_workers.assert_called_once()
    listener.stop.assert_called_once()
    listener.join.assert_called_once()


def test_exit_is_idempotent(mock_dependencies, tmp_path):
    """Repeated _exit calls (e.g. SIGINT then SIGTERM) must not re-run cleanup."""
    from unittest.mock import MagicMock, patch

    app = Maestro(songs_folder=tmp_path)
    app.window = MagicMock()
    listener = MagicMock()
    app._listener = listener

    with patch("PySide6.QtWidgets.QApplication.quit"):
        app._exit()
        app._exit()  # second call from a second signal
        app._exit()  # third for good measure

    # Each cleanup step called exactly once despite three _exit() calls.
    app.window.stop_workers.assert_called_once()
    listener.stop.assert_called_once()
    listener.join.assert_called_once()


