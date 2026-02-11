"""MIDI file parser for Maestro.

Parses MIDI files and extracts note events with timing.
"""

from dataclasses import dataclass
from pathlib import Path

import mido

from maestro.logger import setup_logger

MAX_MIDI_SIZE = 10 * 1024 * 1024  # 10 MB


@dataclass
class Note:
    """A note event with timing information."""

    midi_note: int  # MIDI note number (0-127)
    time: float  # Time in seconds from start of song
    duration: float  # Duration in seconds


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

    file_size = midi_path.stat().st_size
    if file_size > MAX_MIDI_SIZE:
        logger.error(f"MIDI file too large: {file_size} bytes (max {MAX_MIDI_SIZE})")
        raise ValueError(
            f"MIDI file too large: {file_size / (1024 * 1024):.1f} MB (max {MAX_MIDI_SIZE / (1024 * 1024):.0f} MB)"
        )

    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        logger.error(f"Invalid MIDI file '{midi_path}': {e}")
        raise ValueError(f"Invalid MIDI file: {e}") from e

    notes: list[Note] = []
    # Track note_on events to calculate duration
    active_notes: dict[int, tuple[float, int]] = {}  # note -> (start_time, index)

    current_time = 0.0
    current_tempo = 500000  # Default: 120 BPM

    # Merge all tracks and process
    for msg in mido.merge_tracks(mid.tracks):
        # Convert delta time to seconds using current tempo
        current_time += mido.tick2second(msg.time, mid.ticks_per_beat, current_tempo)

        if msg.type == "set_tempo":
            current_tempo = msg.tempo
            continue

        if msg.type == "note_on" and msg.velocity > 0:
            # Note started
            active_notes[msg.note] = (current_time, len(notes))
            notes.append(
                Note(
                    midi_note=msg.note,
                    time=current_time,
                    duration=0.0,  # Will be updated on note_off
                )
            )
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            # Note ended
            if msg.note in active_notes:
                start_time, idx = active_notes.pop(msg.note)
                notes[idx] = Note(
                    midi_note=notes[idx].midi_note,
                    time=notes[idx].time,
                    duration=current_time - start_time,
                )

    return sorted(notes, key=lambda n: n.time)


def get_tempo(mid: mido.MidiFile) -> int:
    """Get tempo from MIDI file, default to 120 BPM."""
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                return int(msg.tempo)
    return 500000  # Default: 120 BPM


def get_midi_info(midi_path: Path) -> dict:
    """Get basic information about a MIDI file.

    Args:
        midi_path: Path to the MIDI file

    Returns:
        Dict with keys: duration (float, seconds), bpm (int), note_count (int)

    Raises:
        ValueError: If file is not a valid MIDI file
        FileNotFoundError: If file doesn't exist
    """
    notes = parse_midi(midi_path)

    # Get tempo for BPM
    try:
        mid = mido.MidiFile(midi_path)
        tempo = get_tempo(mid)
        bpm = round(mido.tempo2bpm(tempo))
    except Exception:
        bpm = 120

    # Calculate duration
    if notes:
        last_note = notes[-1]
        duration = last_note.time + last_note.duration
    else:
        duration = 0.0

    return {
        "duration": duration,
        "bpm": bpm,
        "note_count": len(notes),
    }
