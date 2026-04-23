"""Tests for midi_trim (leading trim + trailing normalization)."""
from __future__ import annotations

from pathlib import Path

import mido
import pytest

from maestro.midi_trim import (
    TAIL_TOLERANCE,
    TARGET_TAIL,
    normalize_trailing_silence,
    trim_leading_silence,
)


def _write_midi(path: Path, first_note_delay_ticks: int, tail_ticks: int) -> None:
    """Create a single-note MIDI with explicit leading delay and trailing silence."""
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=64, time=first_note_delay_ticks))
    track.append(mido.Message("note_off", note=60, velocity=64, time=480))  # 0.5s note
    # end_of_track with extra silence
    track.append(mido.MetaMessage("end_of_track", time=tail_ticks))
    mid.save(path)


def _trailing_seconds(mid: mido.MidiFile) -> float:
    """Return seconds of silence between the last note-off and the end of the longest track."""
    # Find last note-off absolute tick
    latest_off = 0
    end_tick = 0
    for track in mid.tracks:
        cumulative = 0
        last_off = 0
        for msg in track:
            cumulative += msg.time
            if msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                last_off = cumulative
        if last_off > latest_off:
            latest_off = last_off
        if cumulative > end_tick:
            end_tick = cumulative
    tempo = 500000  # default 120 BPM
    silence_ticks = end_tick - latest_off
    return mido.tick2second(silence_ticks, mid.ticks_per_beat, tempo)


def test_pads_short_trailing_silence(tmp_path):
    """A file with <2s trailing silence should be padded to 2s."""
    midi_path = tmp_path / "short_tail.mid"
    # 0.5s tail (240 ticks at 480 tpb / 120 bpm)
    _write_midi(midi_path, first_note_delay_ticks=0, tail_ticks=240)

    before = _trailing_seconds(mido.MidiFile(midi_path))
    assert before < TARGET_TAIL

    changed = normalize_trailing_silence(midi_path)
    assert changed is True

    after = _trailing_seconds(mido.MidiFile(midi_path))
    assert abs(after - TARGET_TAIL) <= TAIL_TOLERANCE + 0.05


def test_trims_long_trailing_silence(tmp_path):
    """A file with >2s trailing silence should be trimmed to 2s."""
    midi_path = tmp_path / "long_tail.mid"
    # 5s tail at 120 bpm = 5 * 2 beats/s * 480 tpb = 4800 ticks
    _write_midi(midi_path, first_note_delay_ticks=0, tail_ticks=4800)

    before = _trailing_seconds(mido.MidiFile(midi_path))
    assert before > TARGET_TAIL

    changed = normalize_trailing_silence(midi_path)
    assert changed is True

    after = _trailing_seconds(mido.MidiFile(midi_path))
    assert abs(after - TARGET_TAIL) <= TAIL_TOLERANCE + 0.05


def test_no_op_when_within_tolerance(tmp_path):
    """A file already at ~2s tail should not be modified."""
    midi_path = tmp_path / "ok_tail.mid"
    # Exactly 2s tail: 2 * 2 beats/s * 480 tpb = 1920 ticks
    _write_midi(midi_path, first_note_delay_ticks=0, tail_ticks=1920)

    mtime_before = midi_path.stat().st_mtime
    changed = normalize_trailing_silence(midi_path)
    assert changed is False
    assert midi_path.stat().st_mtime == mtime_before


def test_no_op_when_no_notes(tmp_path):
    """A file with no note events should be a no-op."""
    midi_path = tmp_path / "silent.mid"
    mid = mido.MidiFile()
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("end_of_track", time=480))
    mid.save(midi_path)

    mtime_before = midi_path.stat().st_mtime
    changed = normalize_trailing_silence(midi_path)
    assert changed is False
    assert midi_path.stat().st_mtime == mtime_before


def test_trim_leading_still_works(tmp_path):
    """Regression: adding trailing normalization didn't break leading trim."""
    midi_path = tmp_path / "leading.mid"
    # 2s leading delay (1920 ticks), 0.5s note, 0.5s tail
    _write_midi(midi_path, first_note_delay_ticks=1920, tail_ticks=240)

    trim_leading_silence(midi_path)

    # After trim, first note should land near TARGET_LEAD (0.1s) — i.e. ~96 ticks.
    mid = mido.MidiFile(midi_path)
    for track in mid.tracks:
        cumulative = 0
        for msg in track:
            cumulative += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                assert cumulative < 200  # ~0.2s worth of ticks
                return
    pytest.fail("no note_on found")
