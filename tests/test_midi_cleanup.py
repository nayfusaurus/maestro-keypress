"""Tests for MIDI post-processing cleanup steps."""

import pretty_midi
import pytest

from maestro.importers.midi_cleanup import (
    MAX_CHORD_SIZE,
    MIN_NOTE_DURATION,
    MIN_VELOCITY,
    cleanup_transcription,
    filter_low_velocity,
    merge_tied_notes,
    quantize_to_grid,
    remove_grace_notes,
    simplify_chords,
)


def _make_midi(*notes_args: tuple[int, int, float, float]) -> pretty_midi.PrettyMIDI:
    """Create a PrettyMIDI with notes. Each tuple is (velocity, pitch, start, end)."""
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0)
    for vel, pitch, start, end in notes_args:
        inst.notes.append(pretty_midi.Note(velocity=vel, pitch=pitch, start=start, end=end))
    pm.instruments.append(inst)
    return pm


# --- filter_low_velocity ---


class TestFilterLowVelocity:
    def test_removes_notes_below_threshold(self):
        pm = _make_midi((10, 60, 0.0, 1.0), (29, 62, 1.0, 2.0), (30, 64, 2.0, 3.0))
        filter_low_velocity(pm)
        assert len(pm.instruments[0].notes) == 1
        assert pm.instruments[0].notes[0].pitch == 64

    def test_keeps_notes_at_threshold(self):
        pm = _make_midi((MIN_VELOCITY, 60, 0.0, 1.0))
        filter_low_velocity(pm)
        assert len(pm.instruments[0].notes) == 1

    def test_no_change_when_all_above(self):
        pm = _make_midi((64, 60, 0.0, 1.0), (127, 62, 1.0, 2.0))
        filter_low_velocity(pm)
        assert len(pm.instruments[0].notes) == 2

    def test_removes_all_when_all_below(self):
        pm = _make_midi((10, 60, 0.0, 1.0), (20, 62, 1.0, 2.0))
        filter_low_velocity(pm)
        assert len(pm.instruments[0].notes) == 0

    def test_handles_empty_instrument(self):
        pm = pretty_midi.PrettyMIDI()
        pm.instruments.append(pretty_midi.Instrument(program=0))
        filter_low_velocity(pm)
        assert len(pm.instruments[0].notes) == 0


# --- remove_grace_notes ---


class TestRemoveGraceNotes:
    def test_removes_short_notes(self):
        pm = _make_midi(
            (64, 60, 0.0, 0.01),  # 10ms — remove
            (64, 62, 1.0, 1.04),  # 40ms — remove
            (64, 64, 2.0, 2.06),  # 60ms — keep
            (64, 65, 3.0, 3.50),  # 500ms — keep
        )
        remove_grace_notes(pm)
        assert len(pm.instruments[0].notes) == 2
        pitches = [n.pitch for n in pm.instruments[0].notes]
        assert pitches == [64, 65]

    def test_keeps_notes_at_threshold(self):
        pm = _make_midi((64, 60, 0.0, MIN_NOTE_DURATION))
        remove_grace_notes(pm)
        assert len(pm.instruments[0].notes) == 1

    def test_preserves_long_notes(self):
        pm = _make_midi((64, 60, 0.0, 0.5), (64, 62, 1.0, 2.0))
        remove_grace_notes(pm)
        assert len(pm.instruments[0].notes) == 2

    def test_removes_all_micro_notes(self):
        pm = _make_midi((64, 60, 0.0, 0.01), (64, 62, 1.0, 1.02))
        remove_grace_notes(pm)
        assert len(pm.instruments[0].notes) == 0

    def test_removes_zero_duration_notes(self):
        pm = _make_midi((64, 60, 1.0, 1.0))
        remove_grace_notes(pm)
        assert len(pm.instruments[0].notes) == 0


# --- merge_tied_notes ---


class TestMergeTiedNotes:
    def test_merges_consecutive_same_pitch_small_gap(self):
        # Two C4 notes with 50ms gap (< 100ms threshold)
        pm = _make_midi((64, 60, 0.0, 1.0), (64, 60, 1.05, 2.0))
        merge_tied_notes(pm)
        notes = pm.instruments[0].notes
        assert len(notes) == 1
        assert notes[0].start == 0.0
        assert notes[0].end == 2.0

    def test_no_merge_when_gap_exceeds_threshold(self):
        # Two C4 notes with 150ms gap (> 100ms threshold)
        pm = _make_midi((64, 60, 0.0, 1.0), (64, 60, 1.15, 2.0))
        merge_tied_notes(pm)
        assert len(pm.instruments[0].notes) == 2

    def test_no_merge_different_pitches(self):
        # C4 and D4 with small gap — different pitches, no merge
        pm = _make_midi((64, 60, 0.0, 1.0), (64, 62, 1.05, 2.0))
        merge_tied_notes(pm)
        assert len(pm.instruments[0].notes) == 2

    def test_merges_chain_of_three(self):
        pm = _make_midi(
            (64, 60, 0.0, 1.0),
            (64, 60, 1.05, 2.0),
            (64, 60, 2.05, 3.0),
        )
        merge_tied_notes(pm)
        notes = pm.instruments[0].notes
        assert len(notes) == 1
        assert notes[0].end == 3.0

    def test_preserves_velocity_of_first_note(self):
        pm = _make_midi((80, 60, 0.0, 1.0), (40, 60, 1.05, 2.0))
        merge_tied_notes(pm)
        assert pm.instruments[0].notes[0].velocity == 80

    def test_handles_overlapping_notes(self):
        # Second note starts before first ends
        pm = _make_midi((64, 60, 0.0, 1.5), (64, 60, 1.0, 2.0))
        merge_tied_notes(pm)
        notes = pm.instruments[0].notes
        assert len(notes) == 1
        assert notes[0].end == 2.0


# --- simplify_chords ---


class TestSimplifyChords:
    def test_simplifies_chord_with_6_notes(self):
        # 6 notes starting at same time → keep 4
        pm = _make_midi(
            (64, 48, 0.0, 1.0),
            (64, 52, 0.0, 1.0),
            (64, 55, 0.0, 1.0),
            (64, 60, 0.0, 1.0),
            (64, 64, 0.0, 1.0),
            (64, 67, 0.0, 1.0),
        )
        simplify_chords(pm)
        notes = pm.instruments[0].notes
        assert len(notes) == MAX_CHORD_SIZE

    def test_preserves_chord_of_4_or_fewer(self):
        pm = _make_midi(
            (64, 48, 0.0, 1.0),
            (64, 52, 0.0, 1.0),
            (64, 55, 0.0, 1.0),
            (64, 60, 0.0, 1.0),
        )
        simplify_chords(pm)
        assert len(pm.instruments[0].notes) == 4

    def test_preserves_single_notes(self):
        pm = _make_midi(
            (64, 60, 0.0, 1.0),
            (64, 62, 2.0, 3.0),
        )
        simplify_chords(pm)
        assert len(pm.instruments[0].notes) == 2

    def test_keeps_root_and_top_3(self):
        # 5 notes: [48, 52, 55, 60, 64] → keep [48, 55, 60, 64]
        pm = _make_midi(
            (64, 48, 0.0, 1.0),
            (64, 52, 0.0, 1.0),
            (64, 55, 0.0, 1.0),
            (64, 60, 0.0, 1.0),
            (64, 64, 0.0, 1.0),
        )
        simplify_chords(pm)
        pitches = sorted(n.pitch for n in pm.instruments[0].notes)
        assert pitches == [48, 55, 60, 64]

    def test_separate_chords_handled_independently(self):
        # Two chords at different times, each with 5 notes
        pm = _make_midi(
            (64, 48, 0.0, 1.0),
            (64, 52, 0.0, 1.0),
            (64, 55, 0.0, 1.0),
            (64, 60, 0.0, 1.0),
            (64, 64, 0.0, 1.0),
            (64, 48, 2.0, 3.0),
            (64, 52, 2.0, 3.0),
            (64, 55, 2.0, 3.0),
            (64, 60, 2.0, 3.0),
            (64, 64, 2.0, 3.0),
        )
        simplify_chords(pm)
        assert len(pm.instruments[0].notes) == 8  # 4 + 4

    def test_chord_boundary_at_threshold(self):
        # Notes within 30ms = same chord, notes 31ms apart = separate
        pm = _make_midi(
            (64, 60, 0.0, 1.0),
            (64, 62, 0.025, 1.0),  # 25ms gap — same chord
            (64, 64, 0.035, 1.0),  # 35ms from first — new chord
        )
        simplify_chords(pm)
        # First chord: [60, 62] (2 notes, no trimming)
        # Second chord: [64] (1 note)
        assert len(pm.instruments[0].notes) == 3


# --- quantize_to_grid ---


class TestQuantizeToGrid:
    def test_snaps_to_nearest_grid(self):
        # At 120 BPM, grid = 60/120/8 = 0.0625s (62.5ms)
        pm = _make_midi((64, 60, 0.07, 0.57))
        quantize_to_grid(pm)
        note = pm.instruments[0].notes[0]
        assert note.start == pytest.approx(0.0625, abs=0.001)
        assert note.end == pytest.approx(0.5625, abs=0.001)

    def test_preserves_minimum_duration(self):
        # Note where start and end snap to same grid point
        pm = _make_midi((64, 60, 0.06, 0.07))  # both snap to 0.0625
        quantize_to_grid(pm)
        note = pm.instruments[0].notes[0]
        assert note.end > note.start

    def test_uses_midi_tempo(self):
        pm = pretty_midi.PrettyMIDI(initial_tempo=60.0)
        inst = pretty_midi.Instrument(program=0)
        inst.notes.append(pretty_midi.Note(velocity=64, pitch=60, start=0.13, end=1.0))
        pm.instruments.append(inst)
        quantize_to_grid(pm)
        # At 60 BPM, grid = 60/60/8 = 0.125s
        assert pm.instruments[0].notes[0].start == pytest.approx(0.125, abs=0.001)

    def test_already_quantized_unchanged(self):
        # At 120 BPM, grid = 0.0625. Note already on grid.
        pm = _make_midi((64, 60, 0.125, 0.5))
        quantize_to_grid(pm)
        note = pm.instruments[0].notes[0]
        assert note.start == pytest.approx(0.125, abs=0.001)
        assert note.end == pytest.approx(0.5, abs=0.001)

    def test_handles_empty_instrument(self):
        pm = pretty_midi.PrettyMIDI()
        pm.instruments.append(pretty_midi.Instrument(program=0))
        quantize_to_grid(pm)
        assert len(pm.instruments[0].notes) == 0


# --- cleanup_transcription ---


class TestCleanupTranscription:
    def test_full_pipeline_reduces_note_count(self):
        pm = _make_midi(
            (10, 60, 0.0, 1.0),  # low velocity — removed
            (64, 62, 1.0, 1.01),  # grace note — removed
            (64, 64, 2.0, 3.0),  # good note — kept
            (64, 64, 3.05, 4.0),  # fragment — merged with above
            (64, 65, 5.0, 6.0),  # good note — kept
        )
        cleanup_transcription(pm)
        notes = pm.instruments[0].notes
        assert len(notes) == 2  # C4 merged + F4

    def test_empty_midi_no_crash(self):
        pm = pretty_midi.PrettyMIDI()
        pm.instruments.append(pretty_midi.Instrument(program=0))
        cleanup_transcription(pm)
        assert len(pm.instruments[0].notes) == 0

    def test_multiple_instruments(self):
        pm = pretty_midi.PrettyMIDI()
        for _ in range(2):
            inst = pretty_midi.Instrument(program=0)
            inst.notes.append(pretty_midi.Note(velocity=10, pitch=60, start=0.0, end=1.0))
            inst.notes.append(pretty_midi.Note(velocity=64, pitch=62, start=1.0, end=2.0))
            pm.instruments.append(inst)
        cleanup_transcription(pm)
        for inst in pm.instruments:
            assert len(inst.notes) == 1
            assert inst.notes[0].pitch == 62
