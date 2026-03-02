"""Tests for Where Winds Meet (WWM) keymap."""

import pytest
from pynput.keyboard import Key

from maestro.keymap_wwm import midi_note_to_key_wwm, midi_note_to_key_wwm_21


class TestNoteMappings36Key:
    """Smoke-check naturals, Shift accidentals, and Ctrl accidentals."""

    @pytest.mark.parametrize(
        "note,expected",
        [
            (48, ("z", None)),  # C3 natural
            (60, ("a", None)),  # C4 natural
            (72, ("q", None)),  # C5 natural
            # Shift accidentals (C#, F#, G#)
            (49, ("z", Key.shift)),  # C#3 → Shift+Z
            (61, ("a", Key.shift)),  # C#4 → Shift+A
            (73, ("q", Key.shift)),  # C#5 → Shift+Q
            (66, ("f", Key.shift)),  # F#4 → Shift+F
            (68, ("g", Key.shift)),  # G#4 → Shift+G
            # Ctrl accidentals (Eb, Bb)
            (51, ("c", Key.ctrl_l)),  # Eb3 → Ctrl+C
            (63, ("d", Key.ctrl_l)),  # Eb4 → Ctrl+D
            (75, ("e", Key.ctrl_l)),  # Eb5 → Ctrl+E
            (58, ("m", Key.ctrl_l)),  # Bb3 → Ctrl+M
            (70, ("j", Key.ctrl_l)),  # Bb4 → Ctrl+J
            (82, ("u", Key.ctrl_l)),  # Bb5 → Ctrl+U
        ],
    )
    def test_naturals_and_accidentals(self, note, expected):
        assert midi_note_to_key_wwm(note) == expected

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key_wwm(47) is None
        assert midi_note_to_key_wwm(84) is None


class TestTranspose36Key:
    """Test octave transposition for out-of-range notes."""

    def test_transpose_below_into_range(self):
        assert midi_note_to_key_wwm(36, transpose=True) == ("z", None)

    def test_transpose_above_into_range(self):
        assert midi_note_to_key_wwm(84, transpose=True) == ("q", None)

    def test_transpose_does_not_affect_in_range(self):
        assert midi_note_to_key_wwm(60, transpose=True) == ("a", None)

    def test_transpose_preserves_shift_modifier(self):
        assert midi_note_to_key_wwm(37, transpose=True) == ("z", Key.shift)

    def test_transpose_preserves_ctrl_modifier(self):
        # MIDI 39 = Eb2, transposes up to Eb3 (MIDI 51)
        assert midi_note_to_key_wwm(39, transpose=True) == ("c", Key.ctrl_l)


class TestNoteMappings21Key:
    """Test 21-key layout: naturals only, no modifiers."""

    @pytest.mark.parametrize(
        "note,expected",
        [
            (48, ("z", None)),  # C3
            (50, ("x", None)),  # D3
            (52, ("c", None)),  # E3
            (60, ("a", None)),  # C4
            (72, ("q", None)),  # C5
            (83, ("u", None)),  # B5
        ],
    )
    def test_naturals_return_key(self, note, expected):
        assert midi_note_to_key_wwm_21(note) == expected

    def test_sharp_skip_returns_none(self):
        assert midi_note_to_key_wwm_21(49, sharp_handling="skip") is None  # C#3
        assert midi_note_to_key_wwm_21(51, sharp_handling="skip") is None  # Eb3
        assert midi_note_to_key_wwm_21(66, sharp_handling="skip") is None  # F#4
        assert midi_note_to_key_wwm_21(70, sharp_handling="skip") is None  # Bb4

    @pytest.mark.parametrize(
        "note,expected_key",
        [
            (49, "z"),  # C#3 → snap to C3
            (51, "x"),  # Eb3 → snap to D3
            (66, "f"),  # F#4 → snap to F4
            (68, "g"),  # G#4 → snap to G4
            (70, "h"),  # Bb4 → snap to A4
        ],
    )
    def test_sharp_snap_maps_to_natural(self, note, expected_key):
        result = midi_note_to_key_wwm_21(note, sharp_handling="snap")
        assert result == (expected_key, None)

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key_wwm_21(47) is None
        assert midi_note_to_key_wwm_21(84) is None


class TestTranspose21Key:
    """Test 21-key transposition."""

    def test_transpose_below(self):
        assert midi_note_to_key_wwm_21(36, transpose=True) == ("z", None)

    def test_transpose_above(self):
        assert midi_note_to_key_wwm_21(84, transpose=True) == ("q", None)

    def test_transpose_sharp_skip(self):
        # MIDI 37 = C#2, transposes to C#3 (49), skip → None
        assert midi_note_to_key_wwm_21(37, transpose=True, sharp_handling="skip") is None

    def test_transpose_sharp_snap(self):
        # MIDI 37 = C#2, transposes to C#3 (49), snap → C3 = "z"
        assert midi_note_to_key_wwm_21(37, transpose=True, sharp_handling="snap") == ("z", None)
