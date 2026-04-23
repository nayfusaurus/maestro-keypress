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

# Trailing-silence normalisation: every file should end with exactly this
# much silence after the last note-off. Files within TAIL_TOLERANCE are
# left untouched so repeated refreshes don't churn mtimes.
TARGET_TAIL = 2.0  # seconds
TAIL_TOLERANCE = 0.05  # seconds


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


def _find_last_note_off_tick(mid: mido.MidiFile) -> int:
    """Return the latest absolute tick at which a note ends across all tracks.

    Treats both note_off and note_on with velocity=0 as note-ends.
    Returns 0 if no note events are found.
    """
    latest = 0
    for track in mid.tracks:
        cumulative = 0
        for msg in track:
            cumulative += msg.time
            is_off = msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0)
            if is_off and cumulative > latest:
                latest = cumulative
    return latest


def _track_total_ticks(track: mido.MidiTrack) -> int:
    """Sum of all message delta-times in a track."""
    return sum(msg.time for msg in track)


def trim_leading_silence(midi_path: Path) -> None:
    """Rewrite ``midi_path`` so its first note_on happens at TARGET_LEAD seconds.

    No-op if the file has no note_on events, or if the computed offset is
    zero or negative (i.e. first note is already at/below target lead).

    Raises:
        FileNotFoundError: If ``midi_path`` does not exist.
        OSError: On I/O failure (permission, disk full, etc.).
        ValueError: On malformed MIDI (propagated from ``mido``).
    """
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

    _atomic_save(mid, midi_path, logger_context="trim_leading_silence")


def _atomic_save(mid: mido.MidiFile, midi_path: Path, logger_context: str) -> None:
    """Write `mid` to `midi_path` atomically via temp file + rename."""
    logger = setup_logger()
    tmp_path = midi_path.with_suffix(midi_path.suffix + ".tmp")
    try:
        mid.save(tmp_path)
        os.replace(tmp_path, midi_path)
    except Exception:
        with contextlib.suppress(OSError):
            tmp_path.unlink(missing_ok=True)
        logger.exception(f"{logger_context} failed for {midi_path}")
        raise


def normalize_trailing_silence(midi_path: Path) -> bool:
    """Rewrite ``midi_path`` so it has exactly ``TARGET_TAIL`` seconds of
    silence after the last note-off across all tracks.

    - Trailing silence shorter than the target: the end-of-track delta is
      extended so the file ends at ``last_note_off + TARGET_TAIL`` ticks.
    - Trailing silence longer than the target: any events past that tick
      are dropped and each track's end-of-track is clamped.
    - Within ``TAIL_TOLERANCE`` of the target: no-op (so repeated refreshes
      don't churn mtimes).

    Returns:
        True if the file was modified, False if it was already within tolerance.
    """
    mid = mido.MidiFile(midi_path)

    last_note_off = _find_last_note_off_tick(mid)
    if last_note_off == 0:
        return False  # no notes → nothing meaningful to pad

    tempo = get_tempo(mid)
    target_ticks = int(mido.second2tick(TARGET_TAIL, mid.ticks_per_beat, tempo))
    tolerance_ticks = int(mido.second2tick(TAIL_TOLERANCE, mid.ticks_per_beat, tempo))
    target_end_tick = last_note_off + target_ticks

    current_end = max((_track_total_ticks(t) for t in mid.tracks), default=0)
    current_trailing = current_end - last_note_off
    if abs(current_trailing - target_ticks) <= tolerance_ticks:
        return False  # already within tolerance

    new_tracks: list[mido.MidiTrack] = []
    for track in mid.tracks:
        new_track = mido.MidiTrack()
        cumulative = 0
        prev_abs = 0
        end_of_track: mido.messages.Message | None = None

        for msg in track:
            cumulative += msg.time
            if msg.type == "end_of_track":
                end_of_track = msg
                continue
            if cumulative > target_end_tick:
                continue  # drop events past the target (trimming case)
            delta = cumulative - prev_abs
            prev_abs = cumulative
            new_track.append(msg.copy(time=delta))

        # Place end_of_track exactly at the target end tick.
        final_delta = max(0, target_end_tick - prev_abs)
        if end_of_track is not None:
            new_track.append(end_of_track.copy(time=final_delta))
        else:
            new_track.append(mido.MetaMessage("end_of_track", time=final_delta))

        new_tracks.append(new_track)

    mid.tracks = new_tracks
    _atomic_save(mid, midi_path, logger_context="normalize_trailing_silence")
    return True
