"""Tests for Where Winds Meet (WWM) keymap."""

import pytest
from pynput.keyboard import Key
from maestro.keymap_wwm import midi_note_to_key_wwm


class TestNaturalNoteMappings:
    """Test natural notes (no Shift modifier) across all octaves."""

    @pytest.mark.parametrize(
        "note,key",
        [
            # Low octave (C3-B3, MIDI 48-59) → Z, X, C, V, B, N, M
            (48, "z"),  # C3
            (50, "x"),  # D3
            (52, "c"),  # E3
            (53, "v"),  # F3
            (55, "b"),  # G3
            (57, "n"),  # A3
            (59, "m"),  # B3
            # Medium octave (C4-B4, MIDI 60-71) → A, S, D, F, G, H, J
            (60, "a"),  # C4
            (62, "s"),  # D4
            (64, "d"),  # E4
            (65, "f"),  # F4
            (67, "g"),  # G4
            (69, "h"),  # A4
            (71, "j"),  # B4
            # High octave (C5-B5, MIDI 72-83) → Q, W, E, R, T, Y, U
            (72, "q"),  # C5
            (74, "w"),  # D5
            (76, "e"),  # E5
            (77, "r"),  # F5
            (79, "t"),  # G5
            (81, "y"),  # A5
            (83, "u"),  # B5
        ],
    )
    def test_natural_notes_no_modifier(self, note, key):
        """Natural notes should map to keys with no Shift modifier."""
        assert midi_note_to_key_wwm(note) == (key, None)


class TestSharpNoteMappings:
    """Test sharp notes (with Shift modifier) across all octaves."""

    @pytest.mark.parametrize(
        "note,key",
        [
            # Low octave sharps (MIDI 49-58)
            (49, "z"),  # C#3
            (51, "x"),  # D#3
            (54, "v"),  # F#3
            (56, "b"),  # G#3
            (58, "n"),  # A#3
            # Medium octave sharps (MIDI 61-70)
            (61, "a"),  # C#4
            (63, "s"),  # D#4
            (66, "f"),  # F#4
            (68, "g"),  # G#4
            (70, "h"),  # A#4
            # High octave sharps (MIDI 73-82)
            (73, "q"),  # C#5
            (75, "w"),  # D#5
            (78, "r"),  # F#5
            (80, "t"),  # G#5
            (82, "y"),  # A#5
        ],
    )
    def test_sharp_notes_with_shift_modifier(self, note, key):
        """Sharp notes should map to keys with Shift modifier."""
        assert midi_note_to_key_wwm(note) == (key, Key.shift)


class TestBoundaries:
    """Test boundary validation at range edges."""

    def test_min_note_boundary(self):
        """Note at MIN (48) should be valid."""
        assert midi_note_to_key_wwm(48) == ("z", None)

    def test_max_note_boundary(self):
        """Note at MAX (83) should be valid."""
        assert midi_note_to_key_wwm(83) == ("u", None)

    def test_note_below_min_is_invalid(self):
        """Note below MIN (47) should return None."""
        assert midi_note_to_key_wwm(47) is None


class TestTranspose:
    """Test transpose behavior for out-of-range notes."""

    def test_transpose_below_into_range(self):
        """C2 (MIDI 36) should transpose up to C3."""
        assert midi_note_to_key_wwm(36, transpose=True) == ("z", None)

    def test_transpose_above_into_range(self):
        """C6 (MIDI 84) should transpose down to C5."""
        assert midi_note_to_key_wwm(84, transpose=True) == ("q", None)

    def test_transpose_does_not_affect_in_range(self):
        """In-range notes should not be affected by transpose."""
        assert midi_note_to_key_wwm(60, transpose=True) == ("a", None)
        assert midi_note_to_key_wwm(72, transpose=True) == ("q", None)

    def test_transpose_preserves_sharp_modifier(self):
        """Transpose should preserve Shift modifier for sharps."""
        # C#2 (MIDI 37) → transpose to C#3 (MIDI 49) → (z, Shift)
        assert midi_note_to_key_wwm(37, transpose=True) == ("z", Key.shift)


class TestOutOfRange:
    """Test out-of-range notes return None when transpose=False."""

    def test_note_below_range(self):
        """MIDI 36 (C2) is below range, should return None."""
        assert midi_note_to_key_wwm(36) is None

    def test_note_above_range(self):
        """MIDI 84 (C6) is above range, should return None."""
        assert midi_note_to_key_wwm(84) is None
