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
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.Message("note_off", note=60, velocity=64, time=480))
    track.append(mido.Message("note_on", note=62, velocity=64, time=0))
    track.append(mido.Message("note_off", note=62, velocity=64, time=480))
    track.append(mido.Message("note_on", note=64, velocity=64, time=0))
    track.append(mido.Message("note_off", note=64, velocity=64, time=480))

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


def test_parse_midi_multi_tempo(tmp_path):
    """Parser should handle tempo changes mid-song."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)

    # Start at 120 BPM (500000 microseconds per beat)
    track.append(mido.MetaMessage("set_tempo", tempo=500000, time=0))
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.Message("note_off", note=60, velocity=64, time=480))

    # Change to 60 BPM (1000000 microseconds per beat)
    track.append(mido.MetaMessage("set_tempo", tempo=1000000, time=0))
    track.append(mido.Message("note_on", note=62, velocity=64, time=0))
    track.append(mido.Message("note_off", note=62, velocity=64, time=480))

    midi_path = tmp_path / "multi_tempo.mid"
    mid.save(midi_path)

    notes = parse_midi(midi_path)
    assert len(notes) == 2

    # First note at 120 BPM: 480 ticks = 0.5 seconds duration
    assert abs(notes[0].duration - 0.5) < 0.01

    # Second note at 60 BPM: 480 ticks = 1.0 seconds duration
    assert abs(notes[1].duration - 1.0) < 0.01


def test_parse_midi_file_size_limit(tmp_path):
    """Parser should reject files larger than MAX_MIDI_SIZE."""
    from maestro.parser import MAX_MIDI_SIZE

    # Create a file larger than the limit
    big_file = tmp_path / "big.mid"
    big_file.write_bytes(b"\x00" * (MAX_MIDI_SIZE + 1))

    with pytest.raises(ValueError, match="too large"):
        parse_midi(big_file)


def test_get_midi_info(test_midi_path):
    """get_midi_info should return song information."""
    from maestro.parser import get_midi_info

    info = get_midi_info(test_midi_path)
    assert "duration" in info
    assert "bpm" in info
    assert "note_count" in info
    assert info["note_count"] == 3
    assert info["bpm"] == 120  # Default BPM
    assert info["duration"] > 0


def test_get_midi_info_nonexistent_file():
    """get_midi_info should raise FileNotFoundError for missing files."""
    from maestro.parser import get_midi_info

    with pytest.raises(FileNotFoundError):
        get_midi_info(Path("/nonexistent/file.mid"))
