"""Integration tests for the full Maestro workflow."""

import pytest
import time
from pathlib import Path
from unittest.mock import patch, Mock
import mido

from maestro.main import Maestro
from maestro.player import PlaybackState


@pytest.fixture
def songs_folder(tmp_path):
    """Create a songs folder with a test MIDI."""
    folder = tmp_path / "songs"
    folder.mkdir()

    # Create a simple test song
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # C major scale
    for note in [60, 62, 64, 65, 67, 69, 71, 72]:
        track.append(mido.Message('note_on', note=note, velocity=64, time=0))
        track.append(mido.Message('note_off', note=note, velocity=64, time=120))

    mid.save(folder / "test_scale.mid")
    return folder


@pytest.fixture
def mock_keyboard():
    """Mock keyboard to avoid actual keypresses."""
    with patch('maestro.player.Controller') as mock:
        yield mock.return_value


@pytest.fixture
def mock_config():
    """Mock config loading/saving."""
    with patch('maestro.main.load_config') as load_mock, \
         patch('maestro.main.save_config') as save_mock, \
         patch('maestro.main.setup_logger') as logger_mock:
        load_mock.return_value = {
            'last_songs_folder': '',
            'game_mode': 'Heartopia',
            'speed': 1.0,
            'preview_lookahead': 5,
        }
        yield {
            'load_config': load_mock,
            'save_config': save_mock,
            'logger': logger_mock.return_value,
        }


def test_full_playback_workflow(songs_folder, mock_keyboard, mock_config):
    """Test loading and playing a song."""
    app = Maestro(songs_folder=songs_folder)

    # Load and play
    song = songs_folder / "test_scale.mid"
    app.player.load(song)
    app.player.play()

    time.sleep(0.1)
    assert app.player.state == PlaybackState.PLAYING

    # Stop
    app.stop()
    assert app.player.state == PlaybackState.STOPPED


def test_song_discovery(songs_folder):
    """Test that songs are discovered from folder."""
    from maestro.gui import get_songs_from_folder

    songs = get_songs_from_folder(songs_folder)
    assert len(songs) == 1
    assert songs[0].name == "test_scale.mid"
