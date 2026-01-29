import pytest
import time
from unittest.mock import Mock, patch
from pathlib import Path

from maestro.player import Player, PlaybackState


@pytest.fixture
def mock_keyboard():
    """Mock pynput keyboard controller."""
    with patch('maestro.player.Controller') as mock:
        yield mock.return_value


@pytest.fixture
def sample_midi(tmp_path):
    """Create a simple test MIDI with multiple notes for longer playback."""
    import mido
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    for i in range(5):
        track.append(mido.Message('note_on', note=60, velocity=64, time=480))
        track.append(mido.Message('note_off', note=60, velocity=64, time=240))
    midi_path = tmp_path / "test.mid"
    mid.save(midi_path)
    return midi_path


def test_player_initial_state():
    """Player should start in STOPPED state."""
    player = Player()
    assert player.state == PlaybackState.STOPPED


def test_player_load_song(sample_midi, mock_keyboard):
    """Player should load a MIDI file."""
    player = Player()
    player.load(sample_midi)
    assert player.current_song == sample_midi


def test_player_play_changes_state(sample_midi, mock_keyboard):
    """Playing should change state to PLAYING."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    assert player.state == PlaybackState.PLAYING
    player.stop()


def test_player_stop_changes_state(sample_midi, mock_keyboard):
    """Stopping should change state to STOPPED."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)
    player.stop()
    assert player.state == PlaybackState.STOPPED


def test_playback_state_has_no_paused():
    """PlaybackState should only have STOPPED and PLAYING."""
    states = [s.name for s in PlaybackState]
    assert 'STOPPED' in states
    assert 'PLAYING' in states
    assert 'PAUSED' not in states
