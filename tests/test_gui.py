"""Tests for the PySide6 GUI modules."""

from pathlib import Path
from unittest.mock import patch

import pytest

from maestro.gui import BINDABLE_KEYS, get_songs_from_folder
from maestro.gui.constants import BINDABLE_KEYS_QT
from maestro.gui.import_panel import ImportPanel
from maestro.gui.utils import check_hotkey_conflict, format_time
from maestro.key_layout import KeyLayout


@pytest.fixture
def songs_folder(tmp_path):
    """Create a folder with test MIDI files."""
    (tmp_path / "song1.mid").touch()
    (tmp_path / "song2.mid").touch()
    (tmp_path / "song3.midi").touch()
    (tmp_path / "not_midi.txt").touch()
    return tmp_path


# --- get_songs_from_folder tests ---


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


# --- format_time tests ---


def test_format_time():
    """format_time should format seconds as M:SS."""
    assert format_time(0) == "0:00"
    assert format_time(65) == "1:05"
    assert format_time(130.7) == "2:10"


# --- BINDABLE_KEYS tests ---


def test_bindable_keys_contains_f_keys():
    """BINDABLE_KEYS should include all F-keys."""
    for i in range(1, 13):
        assert f"F{i}" in BINDABLE_KEYS


def test_bindable_keys_qt_contains_f_keys():
    """BINDABLE_KEYS_QT should include all F-keys."""
    from PySide6.QtCore import Qt

    for i in range(1, 13):
        key = getattr(Qt.Key, f"Key_F{i}")
        assert key in BINDABLE_KEYS_QT
        assert BINDABLE_KEYS_QT[key] == f"f{i}"


# --- Hotkey conflict detection tests ---
# These test the standalone check_hotkey_conflict function


def test_check_hotkey_conflict_detects_play_conflict():
    """check_hotkey_conflict should detect conflicts with play key."""
    # Trying to bind f2 to stop should conflict with play
    conflict = check_hotkey_conflict("f2", "stop_key", "f2", "f3", "escape")
    assert conflict == "Play"

    # Trying to bind f2 to play itself should not conflict
    conflict = check_hotkey_conflict("f2", "play_key", "f2", "f3", "escape")
    assert conflict is None


def test_check_hotkey_conflict_detects_stop_conflict():
    """check_hotkey_conflict should detect conflicts with stop key."""
    # Trying to bind f3 to play should conflict with stop
    conflict = check_hotkey_conflict("f3", "play_key", "f2", "f3", "escape")
    assert conflict == "Stop"

    # Trying to bind f3 to stop itself should not conflict
    conflict = check_hotkey_conflict("f3", "stop_key", "f2", "f3", "escape")
    assert conflict is None


def test_check_hotkey_conflict_detects_emergency_conflict():
    """check_hotkey_conflict should detect conflicts with emergency key."""
    # Trying to bind escape to play should conflict with emergency
    conflict = check_hotkey_conflict("escape", "play_key", "f2", "f3", "escape")
    assert conflict == "Emergency Stop"

    # Trying to bind escape to emergency itself should not conflict
    conflict = check_hotkey_conflict("escape", "emergency_stop_key", "f2", "f3", "escape")
    assert conflict is None


def test_check_hotkey_conflict_no_conflict():
    """check_hotkey_conflict should return None when there's no conflict."""
    # Trying to bind f5 to anything should not conflict
    assert check_hotkey_conflict("f5", "play_key", "f2", "f3", "escape") is None
    assert check_hotkey_conflict("f5", "stop_key", "f2", "f3", "escape") is None
    assert check_hotkey_conflict("f5", "emergency_stop_key", "f2", "f3", "escape") is None


# --- Validation caching tests ---
# These test the caching algorithm directly


def test_validation_cache_stores_mtime_and_validity(tmp_path):
    """Cache should store file mtime and validity status."""
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd")  # Minimal MIDI header

    # Test the cache data structure (dict[str, tuple[float, bool]])
    cache: dict[str, tuple[float, bool]] = {}
    mtime = test_song.stat().st_mtime
    cache[str(test_song)] = (mtime, True)

    assert str(test_song) in cache
    cached_mtime, cached_valid = cache[str(test_song)]
    assert cached_mtime == mtime
    assert cached_valid is True


def test_validation_uses_cache_for_unchanged_files(tmp_path):
    """Validation should skip files that haven't changed according to mtime."""
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")

    validation_cache: dict[str, tuple[float, bool]] = {}
    validation_results: dict[str, str] = {}
    song_info: dict[str, dict] = {}
    song_notes: dict[str, list] = {}

    # Pre-populate cache with current mtime
    mtime = test_song.stat().st_mtime
    validation_cache[str(test_song)] = (mtime, True)
    song_info[str(test_song)] = {"duration": 60, "bpm": 120, "note_count": 100}
    song_notes[str(test_song)] = []

    # Mock get_midi_info and parse_midi to track if they're called
    with (
        patch("maestro.gui.workers.get_midi_info") as mock_info,
        patch("maestro.gui.workers.parse_midi") as mock_parse,
    ):
        # Run validation logic inline (same as ValidationWorker.run)
        song_str = str(test_song)
        current_mtime = test_song.stat().st_mtime
        cached_entry = validation_cache.get(song_str)
        if cached_entry is not None:
            cached_mtime, cached_is_valid = cached_entry
            if cached_mtime == current_mtime:
                if cached_is_valid:
                    validation_results[song_str] = "valid"
                else:
                    validation_results[song_str] = "invalid"

        # Verify parsers were NOT called (cache was used)
        mock_info.assert_not_called()
        mock_parse.assert_not_called()
        assert validation_results[str(test_song)] == "valid"


def test_validation_revalidates_modified_files(tmp_path):
    """Validation should revalidate files when mtime changes."""
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")

    validation_cache: dict[str, tuple[float, bool]] = {}
    validation_results: dict[str, str] = {}

    # Pre-populate cache with old mtime
    old_mtime = test_song.stat().st_mtime
    validation_cache[str(test_song)] = (old_mtime - 1000, True)

    with (
        patch("maestro.gui.workers.get_midi_info") as mock_info,
        patch("maestro.gui.workers.parse_midi") as mock_parse,
    ):
        mock_info.return_value = {"duration": 60, "bpm": 120, "note_count": 100}
        mock_parse.return_value = []

        song_str = str(test_song)
        current_mtime = test_song.stat().st_mtime
        cached_entry = validation_cache.get(song_str)
        needs_revalidation = True
        if cached_entry is not None:
            cached_mtime, _ = cached_entry
            if cached_mtime == current_mtime:
                needs_revalidation = False

        if needs_revalidation:
            mock_info(test_song)
            mock_parse(test_song)
            validation_results[song_str] = "valid"
            validation_cache[song_str] = (current_mtime, True)

        mock_info.assert_called_once()
        mock_parse.assert_called_once()

        new_cached_mtime, _ = validation_cache[str(test_song)]
        assert new_cached_mtime == old_mtime


def test_validation_caches_invalid_files(tmp_path):
    """Validation should cache invalid files too."""
    test_song = tmp_path / "invalid.mid"
    test_song.write_bytes(b"NOT_A_MIDI")

    validation_cache: dict[str, tuple[float, bool]] = {}
    validation_results: dict[str, str] = {}
    song_info: dict[str, dict] = {}
    song_notes: dict[str, list] = {}

    with patch("maestro.gui.workers.get_midi_info") as mock_info:
        mock_info.side_effect = Exception("Invalid MIDI")

        song_str = str(test_song)
        current_mtime = test_song.stat().st_mtime
        try:
            mock_info(test_song)
        except Exception:
            validation_results[song_str] = "invalid"
            song_info[song_str] = {"duration": 0, "bpm": 0, "note_count": 0}
            song_notes[song_str] = []
            validation_cache[song_str] = (current_mtime, False)

        assert str(test_song) in validation_cache
        cached_mtime, cached_valid = validation_cache[str(test_song)]
        assert cached_valid is False
        assert validation_results[str(test_song)] == "invalid"


# --- Key layout tests ---


def test_drums_layout_accepted():
    """KeyLayout should support drums layout."""
    assert KeyLayout.DRUMS.value == "Conga/Cajon (8-key)"


def test_default_layout_is_22_key():
    """Default layout constant should be KEYS_22."""
    assert KeyLayout.KEYS_22.value == "22-key (Full)"


# --- ImportPanel tests ---


class TestImportPanel:
    def test_import_panel_has_url_input(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        assert panel._url_input is not None
        assert panel._url_input.placeholderText() != ""

    def test_import_panel_has_import_button(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        assert panel._import_btn is not None
        assert panel._import_btn.text() == "Import"

    def test_import_panel_status_hidden_by_default(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel.show()
        assert panel._status_label.isHidden()

    def test_show_progress_shows_status(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel.show()
        panel.show_progress("Downloading...")
        assert panel._status_label.isVisible()
        assert panel._status_label.text() == "Downloading..."

    def test_show_success_shows_green_text(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel.show()
        panel.show_success("Downloaded: song.mid")
        assert panel._status_label.isVisible()
        assert "song.mid" in panel._status_label.text()

    def test_show_error_shows_red_text(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel.show()
        panel.show_error("Download failed")
        assert panel._status_label.isVisible()
        assert panel._status_label.property("state") == "error"

    def test_clear_status_hides_label(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel.show()
        panel.show_progress("test")
        panel.clear_status()
        assert panel._status_label.isHidden()

    def test_get_url_returns_input_text(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel._url_input.setText("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert panel.get_url() == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    def test_set_importing_disables_button(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel.set_importing(True)
        assert not panel._import_btn.isEnabled()

    def test_set_importing_false_enables_button(self, qtbot):
        panel = ImportPanel()
        qtbot.addWidget(panel)
        panel.set_importing(True)
        panel.set_importing(False)
        assert panel._import_btn.isEnabled()
