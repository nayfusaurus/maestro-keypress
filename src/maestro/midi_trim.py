"""Trim leading silence from MIDI files.

The validation flow in MainWindow flags files whose first note-on event
occurs later than ``SILENCE_THRESHOLD`` seconds into the song. This
module rewrites such a file in place so the first note lands at
``TARGET_LEAD`` seconds. Meta events (tempo, time signature, key
signature, track name) that lived inside the removed region collapse
onto t=0, preserving their pre-trim final state for the post-trim song.

Writes go through a temp file + ``os.replace`` so a crash mid-write
leaves the original untouched.
"""

from __future__ import annotations

import contextlib
import os
from pathlib import Path

import mido

from maestro.logger import setup_logger
from maestro.parser import get_tempo

SILENCE_THRESHOLD = 0.5  # seconds; files with notes[0].time above this are offenders
TARGET_LEAD = 0.1  # seconds; first note lands here after trim


def _find_first_note_tick(mid: mido.MidiFile) -> int | None:
    """Return the smallest absolute tick across all tracks where a note_on fires."""
    first: int | None = None
    for track in mid.tracks:
        cumulative = 0
        for msg in track:
            cumulative += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                if first is None or cumulative < first:
                    first = cumulative
                break  # only need the first note_on of each track
    return first


def trim_leading_silence(midi_path: Path) -> None:
    """Rewrite ``midi_path`` so its first note_on happens at TARGET_LEAD seconds.

    No-op if the file has no note_on events, or if the computed offset is
    zero or negative (i.e. first note is already at/below target lead).

    Raises:
        FileNotFoundError: If ``midi_path`` does not exist.
        OSError: On I/O failure (permission, disk full, etc.).
        ValueError: On malformed MIDI (propagated from ``mido``).
    """
    logger = setup_logger()

    mid = mido.MidiFile(midi_path)

    first_note_tick = _find_first_note_tick(mid)
    if first_note_tick is None:
        return  # no note_on → nothing to trim

    tempo = get_tempo(mid)  # µs per beat
    target_lead_ticks = int(mido.second2tick(TARGET_LEAD, mid.ticks_per_beat, tempo))
    offset_ticks = first_note_tick - target_lead_ticks
    if offset_ticks <= 0:
        return  # already near target; nothing to trim

    new_tracks: list[mido.MidiTrack] = []
    for track in mid.tracks:
        # Walk in absolute time, shift or clamp each event.
        abs_events: list[tuple[int, mido.messages.Message]] = []
        cumulative = 0
        for msg in track:
            cumulative += msg.time
            new_abs = cumulative - offset_ticks if cumulative >= offset_ticks else 0
            abs_events.append((new_abs, msg))

        # Stable sort so clamped events keep their original order.
        abs_events.sort(key=lambda e: e[0])

        new_track = mido.MidiTrack()
        prev = 0
        for abs_t, msg in abs_events:
            delta = abs_t - prev
            prev = abs_t
            new_track.append(msg.copy(time=delta))
        new_tracks.append(new_track)

    mid.tracks = new_tracks

    # Atomic write via temp file + rename.
    tmp_path = midi_path.with_suffix(midi_path.suffix + ".tmp")
    try:
        mid.save(tmp_path)
        os.replace(tmp_path, midi_path)
    except Exception:
        # Clean up the temp on failure so we don't leave litter.
        with contextlib.suppress(OSError):
            tmp_path.unlink(missing_ok=True)
        logger.exception(f"trim_leading_silence failed for {midi_path}")
        raise
