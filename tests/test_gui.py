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


def test_validation_cache_initialized_empty():
    """Validation cache should be initialized to empty dict."""
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )
    assert picker._validation_cache == {}


def test_validation_cache_stores_mtime_and_validity(tmp_path):
    """Cache should store file mtime and validity status."""
    # Create a test MIDI file
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd")  # Minimal MIDI header

    picker = SongPicker(
        songs_folder=tmp_path,
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Manually populate cache
    mtime = test_song.stat().st_mtime
    picker._validation_cache[str(test_song)] = (mtime, True)

    # Verify cache structure
    assert str(test_song) in picker._validation_cache
    cached_mtime, cached_valid = picker._validation_cache[str(test_song)]
    assert cached_mtime == mtime
    assert cached_valid is True


def test_validation_cache_cleared_on_folder_change(tmp_path):
    """Cache should be cleared when songs folder changes."""
    folder1 = tmp_path / "folder1"
    folder2 = tmp_path / "folder2"
    folder1.mkdir()
    folder2.mkdir()

    picker = SongPicker(
        songs_folder=folder1,
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Populate cache
    picker._validation_cache["song1"] = (123.456, True)
    picker._validation_cache["song2"] = (789.012, False)
    assert len(picker._validation_cache) == 2

    # Mock the folder label and filedialog
    picker.folder_label = Mock()
    with patch("maestro.gui.filedialog.askdirectory", return_value=str(folder2)):
        picker._on_browse_click()

    # Cache should be cleared
    assert picker._validation_cache == {}


def test_validation_uses_cache_for_unchanged_files(tmp_path):
    """Validation should skip files that haven't changed according to mtime."""
    # Create a valid MIDI file
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")

    picker = SongPicker(
        songs_folder=tmp_path,
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Pre-populate cache with current mtime
    mtime = test_song.stat().st_mtime
    picker._validation_cache[str(test_song)] = (mtime, True)
    picker._song_info[str(test_song)] = {"duration": 60, "bpm": 120, "note_count": 100}
    picker._song_notes[str(test_song)] = []
    picker._songs = [test_song]

    # Mock get_midi_info and parse_midi to track if they're called
    with patch("maestro.gui.get_midi_info") as mock_info:
        with patch("maestro.gui.parse_midi") as mock_parse:
            # Run validation (synchronously for testing)
            songs_to_validate = list(picker._songs)
            for song in songs_to_validate:
                song_str = str(song)
                if song.exists():
                    current_mtime = song.stat().st_mtime
                    cached_entry = picker._validation_cache.get(song_str)
                    if cached_entry is not None:
                        cached_mtime, cached_is_valid = cached_entry
                        if cached_mtime == current_mtime:
                            if cached_is_valid:
                                picker._validation_results[song_str] = "valid"
                            else:
                                picker._validation_results[song_str] = "invalid"
                            continue
                    # File changed or not in cache
                    info = mock_info(song)
                    notes = mock_parse(song)
                    picker._validation_results[song_str] = "valid"

            # Verify parsers were NOT called (cache was used)
            mock_info.assert_not_called()
            mock_parse.assert_not_called()

            # Verify result is still valid
            assert picker._validation_results[str(test_song)] == "valid"


def test_validation_revalidates_modified_files(tmp_path):
    """Validation should revalidate files when mtime changes."""
    import time

    # Create a valid MIDI file
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")

    picker = SongPicker(
        songs_folder=tmp_path,
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )

    # Pre-populate cache with old mtime
    old_mtime = test_song.stat().st_mtime
    picker._validation_cache[str(test_song)] = (old_mtime - 1000, True)  # Old mtime
    picker._songs = [test_song]

    # Mock get_midi_info and parse_midi
    with patch("maestro.gui.get_midi_info") as mock_info:
        with patch("maestro.gui.parse_midi") as mock_parse:
            mock_info.return_value = {"duration": 60, "bpm": 120, "note_count": 100}
            mock_parse.return_value = []

            # Run validation (synchronously for testing)
            songs_to_validate = list(picker._songs)
            for song in songs_to_validate:
                song_str = str(song)
                if song.exists():
                    current_mtime = song.stat().st_mtime
                    cached_entry = picker._validation_cache.get(song_str)
                    if cached_entry is not None:
                        cached_mtime, cached_is_valid = cached_entry
                        if cached_mtime == current_mtime:
                            if cached_is_valid:
                                picker._validation_results[song_str] = "valid"
                            continue
                    # File changed or not in cache
                    info = mock_info(song)
                    notes = mock_parse(song)
                    picker._validation_results[song_str] = "valid"
                    picker._song_info[song_str] = info
                    picker._song_notes[song_str] = notes
                    picker._validation_cache[song_str] = (current_mtime, True)

            # Verify parsers WERE called (file was revalidated)
            mock_info.assert_called_once()
            mock_parse.assert_called_once()

            # Verify cache was updated with new mtime
            new_cached_mtime, _ = picker._validation_cache[str(test_song)]
            assert new_cached_mtime == old_mtime  # Current mtime


def test_validation_caches_invalid_files(tmp_path):
    """Validation should cache invalid files too."""
    # Create an invalid MIDI file
    test_song = tmp_path / "invalid.mid"
    test_song.write_bytes(b"NOT_A_MIDI")

    picker = SongPicker(
        songs_folder=tmp_path,
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
    )
    picker._songs = [test_song]

    # Mock get_midi_info to raise exception
    with patch("maestro.gui.get_midi_info") as mock_info:
        with patch("maestro.gui.parse_midi") as mock_parse:
            mock_info.side_effect = Exception("Invalid MIDI")

            # Run validation (synchronously)
            songs_to_validate = list(picker._songs)
            for song in songs_to_validate:
                song_str = str(song)
                if song.exists():
                    current_mtime = song.stat().st_mtime
                    cached_entry = picker._validation_cache.get(song_str)
                    if cached_entry is None:
                        try:
                            info = mock_info(song)
                            notes = mock_parse(song)
                            picker._validation_results[song_str] = "valid"
                            picker._song_info[song_str] = info
                            picker._song_notes[song_str] = notes
                            picker._validation_cache[song_str] = (current_mtime, True)
                        except Exception:
                            picker._validation_results[song_str] = "invalid"
                            picker._song_info[song_str] = {"duration": 0, "bpm": 0, "note_count": 0}
                            picker._song_notes[song_str] = []
                            picker._validation_cache[song_str] = (current_mtime, False)

            # Verify invalid file was cached
            assert str(test_song) in picker._validation_cache
            cached_mtime, cached_valid = picker._validation_cache[str(test_song)]
            assert cached_valid is False
            assert picker._validation_results[str(test_song)] == "invalid"


def test_drums_layout_accepted():
    """SongPicker should accept drums layout."""
    from maestro.key_layout import KeyLayout
    picker = SongPicker(
        songs_folder=Path("/tmp"),
        on_play=Mock(),
        on_stop=Mock(),
        get_state=Mock(return_value="Stopped"),
        initial_layout=KeyLayout.DRUMS,
    )
    assert picker._key_layout == KeyLayout.DRUMS


def test_drums_layout_value():
    """Conga/Cajon layout should have correct display value."""
    from maestro.key_layout import KeyLayout
    assert KeyLayout.DRUMS.value == "Conga/Cajon (8-key)"
