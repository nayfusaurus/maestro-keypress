import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from maestro.gui import SongPicker, get_songs_from_folder


@pytest.fixture
def songs_folder(tmp_path):
    """Create a folder with test MIDI files."""
    (tmp_path / "song1.mid").touch()
    (tmp_path / "song2.mid").touch()
    (tmp_path / "not_midi.txt").touch()
    return tmp_path


def test_get_songs_from_folder(songs_folder):
    """Should return only .mid files."""
    songs = get_songs_from_folder(songs_folder)
    assert len(songs) == 2
    assert all(s.suffix == ".mid" for s in songs)


def test_get_songs_from_empty_folder(tmp_path):
    """Empty folder returns empty list."""
    songs = get_songs_from_folder(tmp_path)
    assert songs == []


def test_get_songs_from_nonexistent_folder():
    """Nonexistent folder returns empty list."""
    songs = get_songs_from_folder(Path("/nonexistent"))
    assert songs == []
