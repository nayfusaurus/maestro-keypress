"""Tests for Heartopia 15-key triple row keymap."""

from maestro.keymap_15_triple import midi_note_to_key_15_triple, NOTE_MAP


class TestRow1Notes:
    """Test Row 1 natural notes: C4=y, D4=u, E4=i, F4=o, G4=p."""

    def test_c4(self):
        """C4 (MIDI 60) should map to Y key."""
        assert midi_note_to_key_15_triple(60) == "y"

    def test_d4(self):
        """D4 (MIDI 62) should map to U key."""
        assert midi_note_to_key_15_triple(62) == "u"

    def test_e4(self):
        """E4 (MIDI 64) should map to I key."""
        assert midi_note_to_key_15_triple(64) == "i"

    def test_f4(self):
        """F4 (MIDI 65) should map to O key."""
        assert midi_note_to_key_15_triple(65) == "o"

    def test_g4(self):
        """G4 (MIDI 67) should map to P key."""
        assert midi_note_to_key_15_triple(67) == "p"


class TestRow2Notes:
    """Test Row 2 natural notes: A4=h, B4=j, C5=k, D5=l, E5=;."""

    def test_a4(self):
        """A4 (MIDI 69) should map to H key."""
        assert midi_note_to_key_15_triple(69) == "h"

    def test_b4(self):
        """B4 (MIDI 71) should map to J key."""
        assert midi_note_to_key_15_triple(71) == "j"

    def test_c5(self):
        """C5 (MIDI 72) should map to K key."""
        assert midi_note_to_key_15_triple(72) == "k"

    def test_d5(self):
        """D5 (MIDI 74) should map to L key."""
        assert midi_note_to_key_15_triple(74) == "l"

    def test_e5(self):
        """E5 (MIDI 76) should map to ; key."""
        assert midi_note_to_key_15_triple(76) == ";"


class TestRow3Notes:
    """Test Row 3 natural notes: F5=n, G5=m, A5=,, B5=., C6=/."""

    def test_f5(self):
        """F5 (MIDI 77) should map to N key."""
        assert midi_note_to_key_15_triple(77) == "n"

    def test_g5(self):
        """G5 (MIDI 79) should map to M key."""
        assert midi_note_to_key_15_triple(79) == "m"

    def test_a5(self):
        """A5 (MIDI 81) should map to , key."""
        assert midi_note_to_key_15_triple(81) == ","

    def test_b5(self):
        """B5 (MIDI 83) should map to . key."""
        assert midi_note_to_key_15_triple(83) == "."

    def test_c6(self):
        """C6 (MIDI 84) should map to / key."""
        assert midi_note_to_key_15_triple(84) == "/"


class TestNoteMapSize:
    """Test NOTE_MAP has exactly 15 entries."""

    def test_note_map_has_15_entries(self):
        """NOTE_MAP should contain exactly 15 key mappings."""
        assert len(NOTE_MAP) == 15


class TestSharpNotesSkip:
    """Test sharp notes return None with default sharp_handling='skip'."""

    def test_c_sharp_4_skip(self):
        """C#4 (MIDI 61) should return None with skip."""
        assert midi_note_to_key_15_triple(61) is None

    def test_d_sharp_4_skip(self):
        """D#4 (MIDI 63) should return None with skip."""
        assert midi_note_to_key_15_triple(63) is None

    def test_f_sharp_4_skip(self):
        """F#4 (MIDI 66) should return None with skip."""
        assert midi_note_to_key_15_triple(66) is None

    def test_g_sharp_4_skip(self):
        """G#4 (MIDI 68) should return None with skip."""
        assert midi_note_to_key_15_triple(68) is None

    def test_a_sharp_4_skip(self):
        """A#4 (MIDI 70) should return None with skip."""
        assert midi_note_to_key_15_triple(70) is None

    def test_c_sharp_5_skip(self):
        """C#5 (MIDI 73) should return None with skip."""
        assert midi_note_to_key_15_triple(73) is None

    def test_f_sharp_5_skip(self):
        """F#5 (MIDI 78) should return None with skip."""
        assert midi_note_to_key_15_triple(78) is None

    def test_g_sharp_5_skip(self):
        """G#5 (MIDI 80) should return None with skip."""
        assert midi_note_to_key_15_triple(80) is None

    def test_a_sharp_5_skip(self):
        """A#5 (MIDI 82) should return None with skip."""
        assert midi_note_to_key_15_triple(82) is None


class TestSharpNotesSnap:
    """Test sharp notes snap to nearest natural with sharp_handling='snap'."""

    def test_c_sharp_4_snaps_to_c4(self):
        """C#4 (MIDI 61) should snap to C4 -> Y key."""
        assert midi_note_to_key_15_triple(61, sharp_handling="snap") == "y"

    def test_d_sharp_4_snaps_to_d4(self):
        """D#4 (MIDI 63) should snap to D4 -> U key."""
        assert midi_note_to_key_15_triple(63, sharp_handling="snap") == "u"

    def test_f_sharp_4_snaps_to_f4(self):
        """F#4 (MIDI 66) should snap to F4 -> O key."""
        assert midi_note_to_key_15_triple(66, sharp_handling="snap") == "o"

    def test_g_sharp_4_snaps_to_g4(self):
        """G#4 (MIDI 68) should snap to G4 -> P key."""
        assert midi_note_to_key_15_triple(68, sharp_handling="snap") == "p"

    def test_a_sharp_4_snaps_to_a4(self):
        """A#4 (MIDI 70) should snap to A4 -> H key."""
        assert midi_note_to_key_15_triple(70, sharp_handling="snap") == "h"

    def test_c_sharp_5_snaps_to_c5(self):
        """C#5 (MIDI 73) should snap to C5 -> K key."""
        assert midi_note_to_key_15_triple(73, sharp_handling="snap") == "k"

    def test_f_sharp_5_snaps_to_f5(self):
        """F#5 (MIDI 78) should snap to F5 -> N key."""
        assert midi_note_to_key_15_triple(78, sharp_handling="snap") == "n"

    def test_g_sharp_5_snaps_to_g5(self):
        """G#5 (MIDI 80) should snap to G5 -> M key."""
        assert midi_note_to_key_15_triple(80, sharp_handling="snap") == "m"

    def test_a_sharp_5_snaps_to_a5(self):
        """A#5 (MIDI 82) should snap to A5 -> , key."""
        assert midi_note_to_key_15_triple(82, sharp_handling="snap") == ","


class TestOutOfRangeNoTranspose:
    """Test out-of-range notes return None when transpose=False."""

    def test_below_range_returns_none(self):
        """MIDI 59 (B3) should return None when below range."""
        assert midi_note_to_key_15_triple(59) is None

    def test_above_range_returns_none(self):
        """MIDI 85 (C#6) should return None when above range."""
        assert midi_note_to_key_15_triple(85) is None

    def test_very_low_returns_none(self):
        """MIDI 24 (C1) should return None when far below range."""
        assert midi_note_to_key_15_triple(24) is None

    def test_very_high_returns_none(self):
        """MIDI 96 (C7) should return None when far above range."""
        assert midi_note_to_key_15_triple(96) is None

    def test_midi_0_returns_none(self):
        """MIDI 0 should return None."""
        assert midi_note_to_key_15_triple(0) is None

    def test_midi_127_returns_none(self):
        """MIDI 127 should return None."""
        assert midi_note_to_key_15_triple(127) is None


class TestTranspose:
    """Test out-of-range notes transpose into range when transpose=True."""

    def test_transpose_one_octave_below(self):
        """C3 (MIDI 48) should transpose up to C4 -> Y key."""
        assert midi_note_to_key_15_triple(48, transpose=True) == "y"

    def test_transpose_two_octaves_below(self):
        """C2 (MIDI 36) should transpose up to C4 -> Y key."""
        assert midi_note_to_key_15_triple(36, transpose=True) == "y"

    def test_transpose_one_octave_above(self):
        """C7 (MIDI 96) should transpose down to C6 -> / key."""
        assert midi_note_to_key_15_triple(96, transpose=True) == "/"

    def test_transpose_two_octaves_above(self):
        """C8 (MIDI 108) should transpose down to C6 -> / key."""
        assert midi_note_to_key_15_triple(108, transpose=True) == "/"

    def test_transpose_sharp_below_range_skip(self):
        """C#3 (MIDI 49) transposed to C#4 (MIDI 61) should return None with skip."""
        assert midi_note_to_key_15_triple(49, transpose=True, sharp_handling="skip") is None

    def test_transpose_sharp_below_range_snap(self):
        """C#3 (MIDI 49) transposed to C#4 (MIDI 61) should snap to C4 -> Y key."""
        assert midi_note_to_key_15_triple(49, transpose=True, sharp_handling="snap") == "y"

    def test_transpose_d5_one_octave_above(self):
        """D6 (MIDI 86) should transpose down to D5 -> L key."""
        assert midi_note_to_key_15_triple(86, transpose=True) == "l"

    def test_transpose_g4_one_octave_below(self):
        """G3 (MIDI 55) should transpose up to G4 -> P key."""
        assert midi_note_to_key_15_triple(55, transpose=True) == "p"

    def test_transpose_in_range_note_unchanged(self):
        """In-range note should not be affected by transpose=True."""
        assert midi_note_to_key_15_triple(60, transpose=True) == "y"

    def test_transpose_very_low_note(self):
        """MIDI 0 (C-1) with transpose should map into range."""
        result = midi_note_to_key_15_triple(0, transpose=True)
        # MIDI 0 is C, should transpose up to C4 or C5 or C6
        assert result in ("y", "k", "/")

    def test_transpose_very_high_note(self):
        """MIDI 127 (G9) with transpose should map into range."""
        result = midi_note_to_key_15_triple(127, transpose=True)
        # MIDI 127 is G, should transpose down to G4 or G5
        assert result in ("p", "m")


class TestTransposeParameter:
    """Tests for the transpose parameter default behavior."""

    def test_transpose_defaults_to_false(self):
        """Default behavior should be transpose=False (returns None for out-of-range)."""
        result = midi_note_to_key_15_triple(96)  # C7, no transpose param
        assert result is None

    def test_transpose_false_returns_key_for_in_range_note(self):
        """With transpose=False, notes in range still return keys."""
        result = midi_note_to_key_15_triple(60, transpose=False)
        assert result == "y"

    def test_sharp_handling_defaults_to_skip(self):
        """Default behavior should be sharp_handling='skip' (returns None for sharps)."""
        result = midi_note_to_key_15_triple(61)  # C#4, no sharp_handling param
        assert result is None


class TestAllNotesMapped:
    """Test all 15 notes in the map are correctly mapped."""

    def test_all_15_notes_produce_keys(self):
        """Every MIDI note in NOTE_MAP should produce a non-None key."""
        for midi_note in NOTE_MAP:
            result = midi_note_to_key_15_triple(midi_note)
            assert result is not None, f"MIDI {midi_note} should map to a key"

    def test_all_keys_are_unique(self):
        """All 15 key mappings should be unique."""
        keys = list(NOTE_MAP.values())
        assert len(keys) == len(set(keys)), "All mapped keys should be unique"

    def test_complete_mapping(self):
        """Verify the complete MIDI-to-key mapping."""
        expected = {
            60: "y", 62: "u", 64: "i", 65: "o", 67: "p",
            69: "h", 71: "j", 72: "k", 74: "l", 76: ";",
            77: "n", 79: "m", 81: ",", 83: ".", 84: "/",
        }
        for midi_note, expected_key in expected.items():
            result = midi_note_to_key_15_triple(midi_note)
            assert result == expected_key, (
                f"MIDI {midi_note} should map to '{expected_key}', got '{result}'"
            )
