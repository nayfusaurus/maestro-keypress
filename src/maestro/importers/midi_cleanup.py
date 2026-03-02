"""Post-processing steps for basic-pitch MIDI transcription output.

Each function modifies a PrettyMIDI object in-place and logs what it changed.
Called from transcribe_audio() after _trim_leading_silence(), before write().
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pretty_midi

# --- Thresholds ---
MIN_VELOCITY = 30  # below this = ghost note (out of 127)
MIN_NOTE_DURATION = 0.05  # 50ms, below = grace note artifact
MERGE_GAP_THRESHOLD = 0.10  # 100ms max gap for tied note merging
CHORD_TIME_WINDOW = 0.03  # 30ms window to group notes as a chord
MAX_CHORD_SIZE = 4  # keep lowest + 3 highest in oversized chords
DEFAULT_BPM = 120.0  # fallback if no tempo in MIDI
QUANTIZE_DIVISIONS = 8  # 32nd note = quarter / 8


def filter_low_velocity(midi_data: pretty_midi.PrettyMIDI) -> None:
    """Remove notes with velocity below MIN_VELOCITY threshold.

    basic-pitch uses velocity as a proxy for detection confidence.
    Low-velocity notes are typically ghost detections from harmonics.
    """
    logger = logging.getLogger("maestro")
    removed = 0
    for inst in midi_data.instruments:
        before = len(inst.notes)
        inst.notes = [n for n in inst.notes if n.velocity >= MIN_VELOCITY]
        removed += before - len(inst.notes)
    if removed:
        logger.info("Velocity filter: removed %d notes with velocity < %d", removed, MIN_VELOCITY)


def remove_grace_notes(midi_data: pretty_midi.PrettyMIDI) -> None:
    """Remove notes shorter than MIN_NOTE_DURATION seconds.

    Eliminates ornamental micro-notes that cause rapid-fire key presses.
    Complements basic-pitch's minimum_note_length parameter.
    """
    logger = logging.getLogger("maestro")
    removed = 0
    for inst in midi_data.instruments:
        before = len(inst.notes)
        inst.notes = [n for n in inst.notes if (n.end - n.start) >= MIN_NOTE_DURATION]
        removed += before - len(inst.notes)
    if removed:
        logger.info(
            "Grace note removal: removed %d notes shorter than %.0fms",
            removed,
            MIN_NOTE_DURATION * 1000,
        )


def merge_tied_notes(midi_data: pretty_midi.PrettyMIDI) -> None:
    """Merge consecutive same-pitch notes separated by less than MERGE_GAP_THRESHOLD.

    Fixes note fragmentation from basic-pitch where a single sustained note
    is split into multiple short notes ("sticky keys" feeling).
    """
    logger = logging.getLogger("maestro")
    merged = 0
    for inst in midi_data.instruments:
        if not inst.notes:
            continue
        sorted_notes = sorted(inst.notes, key=lambda n: (n.pitch, n.start))
        result = [sorted_notes[0]]
        for note in sorted_notes[1:]:
            prev = result[-1]
            if note.pitch == prev.pitch and (note.start - prev.end) < MERGE_GAP_THRESHOLD:
                prev.end = max(prev.end, note.end)
                merged += 1
            else:
                result.append(note)
        inst.notes = result
    if merged:
        logger.info(
            "Tied note merging: merged %d fragmented note pairs (gap < %.0fms)",
            merged,
            MERGE_GAP_THRESHOLD * 1000,
        )


def _trim_chord(notes: list) -> list:
    """If a chord exceeds MAX_CHORD_SIZE, keep lowest + (MAX_CHORD_SIZE-1) highest."""
    if len(notes) <= MAX_CHORD_SIZE:
        return notes
    by_pitch = sorted(notes, key=lambda n: n.pitch)
    return [by_pitch[0]] + by_pitch[-(MAX_CHORD_SIZE - 1) :]


def simplify_chords(midi_data: pretty_midi.PrettyMIDI) -> None:
    """Limit chords to MAX_CHORD_SIZE notes, keeping lowest + highest.

    Groups notes starting within CHORD_TIME_WINDOW as a chord.
    Oversized chords are reduced by dropping middle voices (likely
    harmonics/overtones that basic-pitch falsely detected).
    """
    logger = logging.getLogger("maestro")
    removed = 0
    for inst in midi_data.instruments:
        if not inst.notes:
            continue
        sorted_notes = sorted(inst.notes, key=lambda n: n.start)
        kept: list = []
        group: list = [sorted_notes[0]]
        for note in sorted_notes[1:]:
            if note.start - group[0].start <= CHORD_TIME_WINDOW:
                group.append(note)
            else:
                trimmed = _trim_chord(group)
                removed += len(group) - len(trimmed)
                kept.extend(trimmed)
                group = [note]
        # Process final group
        trimmed = _trim_chord(group)
        removed += len(group) - len(trimmed)
        kept.extend(trimmed)
        inst.notes = kept
    if removed:
        logger.info(
            "Chord simplification: removed %d notes from oversized chords (max %d)",
            removed,
            MAX_CHORD_SIZE,
        )


def quantize_to_grid(midi_data: pretty_midi.PrettyMIDI) -> None:
    """Snap note start/end times to the nearest 32nd note grid.

    Uses the first tempo from the MIDI file, or DEFAULT_BPM if none.
    Ensures minimum note duration of one grid step after snapping.
    """
    logger = logging.getLogger("maestro")
    _, tempi = midi_data.get_tempo_changes()
    bpm = float(tempi[0]) if len(tempi) > 0 else DEFAULT_BPM
    grid = 60.0 / bpm / QUANTIZE_DIVISIONS

    for inst in midi_data.instruments:
        for note in inst.notes:
            note.start = round(note.start / grid) * grid
            note.end = round(note.end / grid) * grid
            if note.end <= note.start:
                note.end = note.start + grid

    logger.info(
        "Beat quantization: snapped to 32nd note grid (BPM=%.0f, grid=%.1fms)",
        bpm,
        grid * 1000,
    )


def cleanup_transcription(midi_data: pretty_midi.PrettyMIDI) -> None:
    """Run all post-processing steps on transcribed MIDI data.

    Steps (in order):
    1. Velocity-based confidence filtering
    2. Grace note removal
    3. Tied note merging
    4. Chord simplification
    5. Beat quantization

    Modifies midi_data in place.
    """
    filter_low_velocity(midi_data)
    remove_grace_notes(midi_data)
    merge_tied_notes(midi_data)
    simplify_chords(midi_data)
    quantize_to_grid(midi_data)
