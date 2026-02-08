"""Tests for Heartopia 15-key double row keymap."""

from maestro.keymap_15_double import (
    midi_note_to_key_15_double,
    ROW_MID,
    ROW_HIGH,
    SHARP_TO_NATURAL,
)


class TestMidRowNaturalNotes:
    """Test mid row natural notes (C4-B4, MIDI 60-71)."""

    def test_mid_c(self):
        """C4 (MIDI 60) should map to A key."""
        assert midi_note_to_key_15_double(60) == "a"

    def test_mid_d(self):
        """D4 (MIDI 62) should map to S key."""
        assert midi_note_to_key_15_double(62) == "s"

    def test_mid_e(self):
        """E4 (MIDI 64) should map to D key."""
        assert midi_note_to_key_15_double(64) == "d"

    def test_mid_f(self):
        """F4 (MIDI 65) should map to F key."""
        assert midi_note_to_key_15_double(65) == "f"

    def test_mid_g(self):
        """G4 (MIDI 67) should map to G key."""
        assert midi_note_to_key_15_double(67) == "g"

    def test_mid_a(self):
        """A4 (MIDI 69) should map to H key."""
        assert midi_note_to_key_15_double(69) == "h"

    def test_mid_b(self):
        """B4 (MIDI 71) should map to J key."""
        assert midi_note_to_key_15_double(71) == "j"


class TestHighRowNaturalNotes:
    """Test high row natural notes (C5-B5, MIDI 72-83)."""

    def test_high_c(self):
        """C5 (MIDI 72) should map to Q key."""
        assert midi_note_to_key_15_double(72) == "q"

    def test_high_d(self):
        """D5 (MIDI 74) should map to W key."""
        assert midi_note_to_key_15_double(74) == "w"

    def test_high_e(self):
        """E5 (MIDI 76) should map to E key."""
        assert midi_note_to_key_15_double(76) == "e"

    def test_high_f(self):
        """F5 (MIDI 77) should map to R key."""
        assert midi_note_to_key_15_double(77) == "r"

    def test_high_g(self):
        """G5 (MIDI 79) should map to T key."""
        assert midi_note_to_key_15_double(79) == "t"

    def test_high_a(self):
        """A5 (MIDI 81) should map to Y key."""
        assert midi_note_to_key_15_double(81) == "y"

    def test_high_b(self):
        """B5 (MIDI 83) should map to U key."""
        assert midi_note_to_key_15_double(83) == "u"


class TestExtendedHighNote:
    """Test extended high note C6 (MIDI 84)."""

    def test_extended_high_c6(self):
        """C6 (MIDI 84) should map to I key."""
        assert midi_note_to_key_15_double(84) == "i"


class TestSharpSkipMode:
    """Test sharp notes return None with default skip mode."""

    def test_mid_c_sharp_skip(self):
        """C#4 (MIDI 61) should return None in skip mode."""
        assert midi_note_to_key_15_double(61) is None

    def test_mid_d_sharp_skip(self):
        """D#4 (MIDI 63) should return None in skip mode."""
        assert midi_note_to_key_15_double(63) is None

    def test_mid_f_sharp_skip(self):
        """F#4 (MIDI 66) should return None in skip mode."""
        assert midi_note_to_key_15_double(66) is None

    def test_mid_g_sharp_skip(self):
        """G#4 (MIDI 68) should return None in skip mode."""
        assert midi_note_to_key_15_double(68) is None

    def test_mid_a_sharp_skip(self):
        """A#4 (MIDI 70) should return None in skip mode."""
        assert midi_note_to_key_15_double(70) is None

    def test_high_c_sharp_skip(self):
        """C#5 (MIDI 73) should return None in skip mode."""
        assert midi_note_to_key_15_double(73) is None

    def test_high_f_sharp_skip(self):
        """F#5 (MIDI 78) should return None in skip mode."""
        assert midi_note_to_key_15_double(78) is None


class TestSharpSnapMode:
    """Test sharp notes snap to nearest natural in snap mode."""

    def test_mid_c_sharp_snaps_to_c(self):
        """C#4 (MIDI 61) should snap to C4 = A key."""
        assert midi_note_to_key_15_double(61, sharp_handling="snap") == "a"

    def test_mid_d_sharp_snaps_to_d(self):
        """D#4 (MIDI 63) should snap to D4 = S key."""
        assert midi_note_to_key_15_double(63, sharp_handling="snap") == "s"

    def test_mid_f_sharp_snaps_to_f(self):
        """F#4 (MIDI 66) should snap to F4 = F key."""
        assert midi_note_to_key_15_double(66, sharp_handling="snap") == "f"

    def test_mid_g_sharp_snaps_to_g(self):
        """G#4 (MIDI 68) should snap to G4 = G key."""
        assert midi_note_to_key_15_double(68, sharp_handling="snap") == "g"

    def test_mid_a_sharp_snaps_to_a(self):
        """A#4 (MIDI 70) should snap to A4 = H key."""
        assert midi_note_to_key_15_double(70, sharp_handling="snap") == "h"

    def test_high_c_sharp_snaps_to_c(self):
        """C#5 (MIDI 73) should snap to C5 = Q key."""
        assert midi_note_to_key_15_double(73, sharp_handling="snap") == "q"

    def test_high_d_sharp_snaps_to_d(self):
        """D#5 (MIDI 75) should snap to D5 = W key."""
        assert midi_note_to_key_15_double(75, sharp_handling="snap") == "w"

    def test_high_f_sharp_snaps_to_f(self):
        """F#5 (MIDI 78) should snap to F5 = R key."""
        assert midi_note_to_key_15_double(78, sharp_handling="snap") == "r"

    def test_high_g_sharp_snaps_to_g(self):
        """G#5 (MIDI 80) should snap to G5 = T key."""
        assert midi_note_to_key_15_double(80, sharp_handling="snap") == "t"

    def test_high_a_sharp_snaps_to_a(self):
        """A#5 (MIDI 82) should snap to A5 = Y key."""
        assert midi_note_to_key_15_double(82, sharp_handling="snap") == "y"


class TestOutOfRangeNoTranspose:
    """Test out-of-range notes return None when transpose=False."""

    def test_below_range_returns_none(self):
        """MIDI 59 (B3) is below range, should return None."""
        assert midi_note_to_key_15_double(59) is None

    def test_far_below_range_returns_none(self):
        """MIDI 36 (C2) is far below range, should return None."""
        assert midi_note_to_key_15_double(36) is None

    def test_above_range_returns_none(self):
        """MIDI 85 (C#6) is above range, should return None."""
        assert midi_note_to_key_15_double(85) is None

    def test_far_above_range_returns_none(self):
        """MIDI 96 (C7) is far above range, should return None."""
        assert midi_note_to_key_15_double(96) is None

    def test_midi_0_returns_none(self):
        """MIDI 0 is far below range, should return None."""
        assert midi_note_to_key_15_double(0) is None

    def test_midi_127_returns_none(self):
        """MIDI 127 is far above range, should return None."""
        assert midi_note_to_key_15_double(127) is None


class TestTranspose:
    """Test out-of-range notes transpose into range when transpose=True."""

    def test_transpose_one_octave_below(self):
        """C3 (MIDI 48) should transpose up to C4 = A key."""
        assert midi_note_to_key_15_double(48, transpose=True) == "a"

    def test_transpose_two_octaves_below(self):
        """C2 (MIDI 36) should transpose up to C4 = A key."""
        assert midi_note_to_key_15_double(36, transpose=True) == "a"

    def test_transpose_one_octave_above(self):
        """C7 (MIDI 96) should transpose down to C6 = I key."""
        assert midi_note_to_key_15_double(96, transpose=True) == "i"

    def test_transpose_two_octaves_above(self):
        """C8 (MIDI 108) should transpose down to C6 = I key."""
        assert midi_note_to_key_15_double(108, transpose=True) == "i"

    def test_transpose_natural_note_below(self):
        """G3 (MIDI 55) should transpose up to G4 = G key."""
        assert midi_note_to_key_15_double(55, transpose=True) == "g"

    def test_transpose_does_not_affect_in_range(self):
        """In-range notes should not be affected by transpose=True."""
        assert midi_note_to_key_15_double(60, transpose=True) == "a"
        assert midi_note_to_key_15_double(72, transpose=True) == "q"
        assert midi_note_to_key_15_double(84, transpose=True) == "i"

    def test_transpose_sharp_below_skip_mode(self):
        """C#3 (MIDI 49) transposes up to C#4, but skip mode returns None."""
        assert midi_note_to_key_15_double(49, transpose=True) is None

    def test_transpose_sharp_below_snap_mode(self):
        """C#3 (MIDI 49) transposes up to C#4, snap mode returns A key."""
        assert midi_note_to_key_15_double(
            49, transpose=True, sharp_handling="snap"
        ) == "a"

    def test_transpose_very_low_note(self):
        """MIDI 0 (C-1) should transpose into range."""
        key = midi_note_to_key_15_double(0, transpose=True)
        # MIDI 0 is C, should end up as C in one of our rows
        assert key in ("a", "q", "i")

    def test_transpose_very_high_note(self):
        """MIDI 127 (G9) should transpose into range."""
        key = midi_note_to_key_15_double(127, transpose=True)
        # MIDI 127 is G, should end up as G in one of our rows
        assert key in ("g", "t")


class TestTransposeParameter:
    """Tests for the transpose parameter defaults."""

    def test_transpose_defaults_to_false(self):
        """Default behavior should be transpose=False (returns None for out-of-range)."""
        assert midi_note_to_key_15_double(96) is None

    def test_transpose_false_returns_none_for_high_note(self):
        """With transpose=False, notes above range return None."""
        assert midi_note_to_key_15_double(96, transpose=False) is None

    def test_transpose_false_returns_none_for_low_note(self):
        """With transpose=False, notes below range return None."""
        assert midi_note_to_key_15_double(36, transpose=False) is None

    def test_transpose_false_returns_key_for_in_range_note(self):
        """With transpose=False, notes in range still return keys."""
        assert midi_note_to_key_15_double(60, transpose=False) == "a"


class TestRowSizes:
    """Test that ROW_MID and ROW_HIGH have the correct number of entries."""

    def test_row_mid_has_7_entries(self):
        """ROW_MID should have 7 entries (7 natural notes)."""
        assert len(ROW_MID) == 7

    def test_row_high_has_7_entries(self):
        """ROW_HIGH should have 7 entries (7 natural notes)."""
        assert len(ROW_HIGH) == 7


class TestSharpSnapMappings:
    """Test all entries in SHARP_TO_NATURAL mapping."""

    def test_c_sharp_maps_to_c(self):
        """Offset 1 (C#) should map to offset 0 (C)."""
        assert SHARP_TO_NATURAL[1] == 0

    def test_d_sharp_maps_to_d(self):
        """Offset 3 (D#) should map to offset 2 (D)."""
        assert SHARP_TO_NATURAL[3] == 2

    def test_f_sharp_maps_to_f(self):
        """Offset 6 (F#) should map to offset 5 (F)."""
        assert SHARP_TO_NATURAL[6] == 5

    def test_g_sharp_maps_to_g(self):
        """Offset 8 (G#) should map to offset 7 (G)."""
        assert SHARP_TO_NATURAL[8] == 7

    def test_a_sharp_maps_to_a(self):
        """Offset 10 (A#) should map to offset 9 (A)."""
        assert SHARP_TO_NATURAL[10] == 9

    def test_sharp_to_natural_has_5_entries(self):
        """SHARP_TO_NATURAL should have exactly 5 entries (5 sharp notes)."""
        assert len(SHARP_TO_NATURAL) == 5
