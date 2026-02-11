import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from maestro.gui import SongPicker, get_songs_from_folder


@pytest.fixture
def songs_folder(tmp_path):
    """Create a folder with test MIDI files."""
    (tmp_path / "song1.mid").touch()
    (tmp_path / "song2.mid").touch()
    (tmp_path / "song3.midi").touch()
    (tmp_path / "not_midi.txt").touch()
    return tmp_path


def test_get_songs_from_folder(songs_folder):
    """Should return both .mid and .midi files."""
    songs = get_songs_from_folder(songs_folder)
    assert len(songs) == 3
    assert all(s.suffix in [".mid", ".midi"] for s in songs)
    # Verify both extensions are present
    suffixes = [s.suffix for s in songs]
    assert ".mid" in suffixes
    assert ".midi" in suffixes


def test_get_songs_from_empty_folder(tmp_path):
    """Empty folder returns empty list."""
    songs = get_songs_from_folder(tmp_path)
    assert songs == []


def test_get_songs_from_nonexistent_folder():
    """Nonexistent folder returns empty list."""
    songs = get_songs_from_folder(Path("/nonexistent"))
    assert songs == []


def test_on_folder_change_callback():
    """SongPicker should accept on_folder_change callback."""
    callback = Mock()
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        on_folder_change=callback,
    )
    assert picker.on_folder_change == callback


def test_on_layout_change_callback():
    """SongPicker should accept on_layout_change callback."""
    from maestro.key_layout import KeyLayout
    callback = Mock()
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        on_layout_change=callback,
        initial_layout=KeyLayout.KEYS_15_DOUBLE,
    )
    assert picker.on_layout_change == callback
    assert picker._key_layout == KeyLayout.KEYS_15_DOUBLE


def test_default_layout_is_22_key():
    """Default layout should be 22-key."""
    from maestro.key_layout import KeyLayout
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )
    assert picker._key_layout == KeyLayout.KEYS_22


def test_song_picker_accepts_note_compatibility_callback():
    """SongPicker should accept get_note_compatibility callback."""
    callback = Mock(return_value=(10, 15))
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        get_note_compatibility=callback,
    )
    assert picker.get_note_compatibility == callback


def test_validation_results_initialized_empty():
    """Validation results should start empty."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )
    assert picker._validation_results == {}
    assert picker._song_info == {}


def test_song_picker_accepts_favorites_callbacks():
    """SongPicker should accept favorite-related callbacks."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        on_favorite_toggle=Mock(),
        get_favorites=Mock(return_value=["song1"]),
    )
    assert picker.on_favorite_toggle is not None
    assert picker.get_favorites is not None


def test_song_picker_accepts_sharp_handling():
    """SongPicker should accept sharp handling callbacks."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        on_sharp_handling_change=Mock(),
        initial_sharp_handling="snap",
    )
    assert picker._sharp_handling == "snap"


def test_prev_state_initialized():
    """Previous state should be initialized to Stopped."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )
    assert picker._prev_state == "Stopped"


def test_song_picker_accepts_hotkey_callbacks():
    """SongPicker should accept hotkey remapping callbacks."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        on_hotkey_change=Mock(),
        initial_play_key="f5",
        initial_stop_key="f6",
        initial_emergency_key="home",
    )
    assert picker._play_key == "f5"
    assert picker._stop_key == "f6"
    assert picker._emergency_key == "home"


def test_bindable_keys_contains_f_keys():
    """BINDABLE_KEYS should include all F-keys."""
    from maestro.gui import BINDABLE_KEYS

    for i in range(1, 13):
        assert f"F{i}" in BINDABLE_KEYS


def test_check_hotkey_conflict_detects_play_conflict():
    """_check_hotkey_conflict should detect conflicts with play key."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        initial_play_key="f2",
        initial_stop_key="f3",
        initial_emergency_key="escape",
    )

    # Trying to bind f2 to stop should conflict with play
    conflict = picker._check_hotkey_conflict("f2", "stop_key")
    assert conflict == "Play"

    # Trying to bind f2 to play itself should not conflict
    conflict = picker._check_hotkey_conflict("f2", "play_key")
    assert conflict is None


def test_check_hotkey_conflict_detects_stop_conflict():
    """_check_hotkey_conflict should detect conflicts with stop key."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        initial_play_key="f2",
        initial_stop_key="f3",
        initial_emergency_key="escape",
    )

    # Trying to bind f3 to play should conflict with stop
    conflict = picker._check_hotkey_conflict("f3", "play_key")
    assert conflict == "Stop"

    # Trying to bind f3 to stop itself should not conflict
    conflict = picker._check_hotkey_conflict("f3", "stop_key")
    assert conflict is None


def test_check_hotkey_conflict_detects_emergency_conflict():
    """_check_hotkey_conflict should detect conflicts with emergency key."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        initial_play_key="f2",
        initial_stop_key="f3",
        initial_emergency_key="escape",
    )

    # Trying to bind escape to play should conflict with emergency
    conflict = picker._check_hotkey_conflict("escape", "play_key")
    assert conflict == "Emergency Stop"

    # Trying to bind escape to emergency itself should not conflict
    conflict = picker._check_hotkey_conflict("escape", "emergency_stop_key")
    assert conflict is None


def test_check_hotkey_conflict_no_conflict():
    """_check_hotkey_conflict should return None when there's no conflict."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        initial_play_key="f2",
        initial_stop_key="f3",
        initial_emergency_key="escape",
    )

    # Trying to bind f5 to anything should not conflict
    assert picker._check_hotkey_conflict("f5", "play_key") is None
    assert picker._check_hotkey_conflict("f5", "stop_key") is None
    assert picker._check_hotkey_conflict("f5", "emergency_stop_key") is None


def test_auto_minimized_initialized_false():
    """Auto-minimized flag should be initialized to False."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )
    assert picker._auto_minimized is False


def test_auto_minimized_set_on_play():
    """Auto-minimized flag should be set to True when play is clicked."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Create mock window
    picker.window = Mock()
    picker.song_listbox = Mock()
    picker._filtered_songs = [Path("/tmp/song.mid")]
    picker.song_listbox.curselection.return_value = [0]

    # Call play
    picker._on_play_click()

    # Verify window was minimized and flag was set
    picker.window.iconify.assert_called_once()
    assert picker._auto_minimized is True


def test_auto_minimized_reset_on_song_finish():
    """Auto-minimized flag should be reset when song finishes."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Create mock window and set flag
    picker.window = Mock()
    picker._auto_minimized = True
    picker.status_label = Mock()

    # Call song finished
    picker._on_song_finished()

    # Verify window was restored and flag was reset
    picker.window.deiconify.assert_called_once()
    picker.window.lift.assert_called_once()
    assert picker._auto_minimized is False


def test_window_not_restored_if_not_auto_minimized():
    """Window should not be restored if it wasn't auto-minimized."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Create mock window but keep flag False (user manually minimized)
    picker.window = Mock()
    picker._auto_minimized = False
    picker.status_label = Mock()

    # Call song finished
    picker._on_song_finished()

    # Verify window was NOT restored
    picker.window.deiconify.assert_not_called()
    picker.window.lift.assert_not_called()


def test_window_restore_handles_no_window():
    """Song finished should handle case where window is None."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Set flag but no window
    picker._auto_minimized = True
    picker.window = None
    picker.status_label = Mock()

    # Should not crash
    picker._on_song_finished()
