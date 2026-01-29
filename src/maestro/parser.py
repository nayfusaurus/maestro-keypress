"""MIDI file parser for Maestro.

Parses MIDI files and extracts note events with timing.
"""

from dataclasses import dataclass
from pathlib import Path

import mido

from maestro.logger import setup_logger


@dataclass
class Note:
    """A note event with timing information."""
    midi_note: int  # MIDI note number (0-127)
    time: float     # Time in seconds from start of song
    duration: float # Duration in seconds


def parse_midi(midi_path: Path) -> list[Note]:
    """Parse a MIDI file and extract notes with timing.

    Args:
        midi_path: Path to the MIDI file

    Returns:
        List of Note objects sorted by time

    Raises:
        ValueError: If file is not a valid MIDI file
        FileNotFoundError: If file doesn't exist
    """
    logger = setup_logger()

    if not midi_path.exists():
        logger.error(f"MIDI file not found: {midi_path}")
        raise FileNotFoundError(f"MIDI file not found: {midi_path}")

    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        logger.error(f"Invalid MIDI file '{midi_path}': {e}")
        raise ValueError(f"Invalid MIDI file: {e}")

    notes = []
    # Track note_on events to calculate duration
    active_notes: dict[int, tuple[float, int]] = {}  # note -> (start_time, index)

    current_time = 0.0

    # Merge all tracks and process
    for msg in mido.merge_tracks(mid.tracks):
        # Convert delta time to seconds
        current_time += mido.tick2second(msg.time, mid.ticks_per_beat, get_tempo(mid))

        if msg.type == 'note_on' and msg.velocity > 0:
            # Note started
            active_notes[msg.note] = (current_time, len(notes))
            notes.append(Note(
                midi_note=msg.note,
                time=current_time,
                duration=0.0  # Will be updated on note_off
            ))
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            # Note ended
            if msg.note in active_notes:
                start_time, idx = active_notes.pop(msg.note)
                notes[idx] = Note(
                    midi_note=notes[idx].midi_note,
                    time=notes[idx].time,
                    duration=current_time - start_time
                )

    return sorted(notes, key=lambda n: n.time)


def get_tempo(mid: mido.MidiFile) -> int:
    """Get tempo from MIDI file, default to 120 BPM."""
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return msg.tempo
    return 500000  # Default: 120 BPM
