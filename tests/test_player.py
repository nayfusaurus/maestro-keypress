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


def test_speed_clamped_to_valid_range():
    """Speed should be clamped between 0.25 and 1.5."""
    player = Player()

    player.speed = 0.1  # Below min
    assert player.speed == 0.25

    player.speed = 2.0  # Above max
    assert player.speed == 1.5

    player.speed = 1.0  # Valid
    assert player.speed == 1.0


def test_get_upcoming_notes_returns_notes_within_lookahead(sample_midi, mock_keyboard):
    """get_upcoming_notes should return notes within lookahead window."""
    player = Player()
    player.load(sample_midi)
    player.play()
    time.sleep(0.1)

    notes = player.get_upcoming_notes(5.0)
    assert isinstance(notes, list)
    player.stop()


def test_get_upcoming_notes_empty_when_stopped():
    """get_upcoming_notes should return empty list when stopped."""
    player = Player()
    notes = player.get_upcoming_notes(5.0)
    assert notes == []


def test_duration_includes_last_note_duration(tmp_path, mock_keyboard):
    """Duration should include the last note's duration, not just its start time."""
    import mido
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    # Single note: starts at 0, duration of 480 ticks
    # At 120 BPM with 480 ticks/beat: 480 ticks = 0.5 seconds
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
    track.append(mido.Message('note_off', note=60, velocity=64, time=480))
    midi_path = tmp_path / "duration_test.mid"
    mid.save(midi_path)

    player = Player()
    player.load(midi_path)

    # Note starts at 0, lasts 0.5 seconds
    # Duration should be ~0.5, not 0.0
    assert player.duration >= 0.4  # Allow small float variance
    assert player.duration <= 0.6


class TestTransposeProperty:
    """Tests for the transpose property."""

    def test_transpose_default_is_false(self):
        """Player should default to transpose=False."""
        player = Player()
        assert player.transpose is False

    def test_transpose_can_be_set_to_true(self):
        """Player transpose can be enabled."""
        player = Player()
        player.transpose = True
        assert player.transpose is True

    def test_transpose_can_be_set_to_false(self):
        """Player transpose can be disabled."""
        player = Player()
        player.transpose = True
        player.transpose = False
        assert player.transpose is False
