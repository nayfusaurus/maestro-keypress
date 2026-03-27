"""Tests for the PySide6 GUI modules."""

from pathlib import Path
from unittest.mock import patch

import pytest

from maestro.gui import get_songs_from_folder
from maestro.gui.utils import check_hotkey_conflict, format_time


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


# --- Hotkey conflict detection tests ---


def test_check_hotkey_conflict_detects_play_conflict():
    conflict = check_hotkey_conflict("f2", "stop_key", "f2", "f3", "escape")
    assert conflict == "Play"
    assert check_hotkey_conflict("f2", "play_key", "f2", "f3", "escape") is None


def test_check_hotkey_conflict_detects_stop_conflict():
    conflict = check_hotkey_conflict("f3", "play_key", "f2", "f3", "escape")
    assert conflict == "Stop"
    assert check_hotkey_conflict("f3", "stop_key", "f2", "f3", "escape") is None


def test_check_hotkey_conflict_detects_emergency_conflict():
    conflict = check_hotkey_conflict("escape", "play_key", "f2", "f3", "escape")
    assert conflict == "Emergency Stop"
    assert check_hotkey_conflict("escape", "emergency_stop_key", "f2", "f3", "escape") is None


def test_check_hotkey_conflict_no_conflict():
    assert check_hotkey_conflict("f5", "play_key", "f2", "f3", "escape") is None
    assert check_hotkey_conflict("f5", "stop_key", "f2", "f3", "escape") is None


# --- Validation caching tests ---


def test_validation_uses_cache_for_unchanged_files(tmp_path):
    """Validation should skip files that haven't changed according to mtime."""
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")

    validation_cache: dict[str, tuple[float, bool]] = {}
    validation_results: dict[str, str] = {}
    song_info: dict[str, dict] = {}
    song_notes: dict[str, list] = {}

    mtime = test_song.stat().st_mtime
    validation_cache[str(test_song)] = (mtime, True)
    song_info[str(test_song)] = {"duration": 60, "bpm": 120, "note_count": 100}
    song_notes[str(test_song)] = []

    with (
        patch("maestro.gui.workers.get_midi_info") as mock_info,
        patch("maestro.gui.workers.parse_midi") as mock_parse,
    ):
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

        mock_info.assert_not_called()
        mock_parse.assert_not_called()
        assert validation_results[str(test_song)] == "valid"


def test_validation_revalidates_modified_files(tmp_path):
    """Validation should revalidate files when mtime changes."""
    test_song = tmp_path / "test.mid"
    test_song.write_bytes(b"MThd\x00\x00\x00\x06\x00\x00\x00\x01\x00\x60")

    validation_cache: dict[str, tuple[float, bool]] = {}
    validation_results: dict[str, str] = {}

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

    with patch("maestro.gui.workers.get_midi_info") as mock_info:
        mock_info.side_effect = Exception("Invalid MIDI")

        song_str = str(test_song)
        current_mtime = test_song.stat().st_mtime
        try:
            mock_info(test_song)
        except Exception:
            validation_results[song_str] = "invalid"
            validation_cache[song_str] = (current_mtime, False)

        assert str(test_song) in validation_cache
        _, cached_valid = validation_cache[str(test_song)]
        assert cached_valid is False
        assert validation_results[str(test_song)] == "invalid"
