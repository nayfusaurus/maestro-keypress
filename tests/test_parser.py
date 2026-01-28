# tests/test_parser.py
import pytest
from pathlib import Path
import mido

from maestro.parser import parse_midi, Note


@pytest.fixture
def test_midi_path(tmp_path):
    """Create a simple test MIDI file."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Add some notes: C4, D4, E4 with timing
    track.append(mido.Message('note_on', note=60, velocity=64, time=0))
    track.append(mido.Message('note_off', note=60, velocity=64, time=480))
    track.append(mido.Message('note_on', note=62, velocity=64, time=0))
    track.append(mido.Message('note_off', note=62, velocity=64, time=480))
    track.append(mido.Message('note_on', note=64, velocity=64, time=0))
    track.append(mido.Message('note_off', note=64, velocity=64, time=480))

    midi_path = tmp_path / "test_song.mid"
    mid.save(midi_path)
    return midi_path


def test_parse_midi_returns_notes(test_midi_path):
    """parse_midi should return a list of Note objects."""
    notes = parse_midi(test_midi_path)
    assert len(notes) == 3
    assert all(isinstance(n, Note) for n in notes)


def test_parse_midi_note_values(test_midi_path):
    """Notes should have correct MIDI values."""
    notes = parse_midi(test_midi_path)
    assert notes[0].midi_note == 60
    assert notes[1].midi_note == 62
    assert notes[2].midi_note == 64


def test_parse_midi_timing(test_midi_path):
    """Notes should have timing in seconds."""
    notes = parse_midi(test_midi_path)
    # First note starts at 0
    assert notes[0].time == 0.0
    # Subsequent notes have increasing times
    assert notes[1].time > notes[0].time
    assert notes[2].time > notes[1].time


def test_parse_midi_invalid_file():
    """Invalid file should raise ValueError."""
    with pytest.raises((ValueError, FileNotFoundError)):
        parse_midi(Path("/nonexistent/file.mid"))
