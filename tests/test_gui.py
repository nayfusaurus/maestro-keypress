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
