"""Tests for Heartopia 8-key drum keymap."""

from maestro.keymap_drums import (
    midi_note_to_key,
    KEYMAP_DRUMS,
    MIN_NOTE,
    MAX_NOTE,
)


class TestDrumNotes:
    """Test all 8 drum notes map correctly (MIDI 60-67)."""

    def test_note_60_maps_to_y(self):
        """C4 (MIDI 60) should map to Y key."""
        assert midi_note_to_key(60) == "y"

    def test_note_61_maps_to_u(self):
        """C#4 (MIDI 61) should map to U key."""
        assert midi_note_to_key(61) == "u"

    def test_note_62_maps_to_i(self):
        """D4 (MIDI 62) should map to I key."""
        assert midi_note_to_key(62) == "i"

    def test_note_63_maps_to_o(self):
        """D#4 (MIDI 63) should map to O key."""
        assert midi_note_to_key(63) == "o"

    def test_note_64_maps_to_h(self):
        """E4 (MIDI 64) should map to H key."""
        assert midi_note_to_key(64) == "h"

    def test_note_65_maps_to_j(self):
        """F4 (MIDI 65) should map to J key."""
        assert midi_note_to_key(65) == "j"

    def test_note_66_maps_to_k(self):
        """F#4 (MIDI 66) should map to K key."""
        assert midi_note_to_key(66) == "k"

    def test_note_67_maps_to_l(self):
        """G4 (MIDI 67) should map to L key."""
        assert midi_note_to_key(67) == "l"


class TestConstants:
    """Test MIN_NOTE and MAX_NOTE constants."""

    def test_min_note_is_60(self):
        """MIN_NOTE should be 60 (C4)."""
        assert MIN_NOTE == 60

    def test_max_note_is_67(self):
        """MAX_NOTE should be 67 (G4)."""
        assert MAX_NOTE == 67


class TestKeymapSize:
    """Test KEYMAP_DRUMS has exactly 8 entries."""

    def test_keymap_has_8_entries(self):
        """KEYMAP_DRUMS should have exactly 8 entries (60-67 inclusive)."""
        assert len(KEYMAP_DRUMS) == 8

    def test_keymap_contains_all_notes_in_range(self):
        """KEYMAP_DRUMS should contain all notes from 60 to 67."""
        for note in range(MIN_NOTE, MAX_NOTE + 1):
            assert note in KEYMAP_DRUMS


class TestOutOfRange:
    """Test out-of-range notes return None."""

    def test_note_59_returns_none(self):
        """MIDI 59 (B3) is below range, should return None."""
        assert midi_note_to_key(59) is None

    def test_note_68_returns_none(self):
        """MIDI 68 (G#4) is above range, should return None."""
        assert midi_note_to_key(68) is None

    def test_far_below_range_returns_none(self):
        """MIDI 36 (C2) is far below range, should return None."""
        assert midi_note_to_key(36) is None

    def test_far_above_range_returns_none(self):
        """MIDI 96 (C7) is far above range, should return None."""
        assert midi_note_to_key(96) is None


class TestEdgeCases:
    """Test edge cases (MIDI 0, MIDI 127)."""

    def test_midi_0_returns_none(self):
        """MIDI 0 is far below range, should return None."""
        assert midi_note_to_key(0) is None

    def test_midi_127_returns_none(self):
        """MIDI 127 is far above range, should return None."""
        assert midi_note_to_key(127) is None


class TestTransposeParameter:
    """Test transpose parameter is accepted but ignored for drums."""

    def test_transpose_true_ignored_for_note_60(self):
        """Transpose=True should have no effect on drums (note 60)."""
        assert midi_note_to_key(60, transpose=True) == "y"

    def test_transpose_true_ignored_for_note_67(self):
        """Transpose=True should have no effect on drums (note 67)."""
        assert midi_note_to_key(67, transpose=True) == "l"

    def test_transpose_false_explicit(self):
        """Transpose=False should work normally."""
        assert midi_note_to_key(60, transpose=False) == "y"

    def test_transpose_does_not_affect_out_of_range_low(self):
        """Transpose=True should not transpose notes below range."""
        # Unlike piano keymaps, drums don't transpose
        assert midi_note_to_key(48, transpose=True) is None

    def test_transpose_does_not_affect_out_of_range_high(self):
        """Transpose=True should not transpose notes above range."""
        # Unlike piano keymaps, drums don't transpose
        assert midi_note_to_key(79, transpose=True) is None

    def test_transpose_defaults_to_false(self):
        """Default behavior should be transpose=False (no difference for drums)."""
        # Default call should work the same as explicit False
        assert midi_note_to_key(60) == midi_note_to_key(60, transpose=False)


class TestReturnType:
    """Test all valid notes return strings (not KeyCode objects)."""

    def test_returns_string_for_note_60(self):
        """midi_note_to_key should return str type for valid note."""
        result = midi_note_to_key(60)
        assert isinstance(result, str)

    def test_returns_string_for_note_67(self):
        """midi_note_to_key should return str type for max valid note."""
        result = midi_note_to_key(67)
        assert isinstance(result, str)

    def test_returns_string_for_all_valid_notes(self):
        """All valid notes should return str type."""
        for note in range(MIN_NOTE, MAX_NOTE + 1):
            result = midi_note_to_key(note)
            assert isinstance(result, str), f"Note {note} did not return str"

    def test_all_keys_are_lowercase(self):
        """All returned keys should be lowercase letters."""
        for note in range(MIN_NOTE, MAX_NOTE + 1):
            key = midi_note_to_key(note)
            assert key.islower(), f"Key '{key}' for note {note} is not lowercase"
            assert len(key) == 1, f"Key '{key}' for note {note} is not single char"


class TestKeymapIntegrity:
    """Test internal consistency of KEYMAP_DRUMS."""

    def test_all_keys_are_unique(self):
        """All keyboard keys in KEYMAP_DRUMS should be unique."""
        keys = list(KEYMAP_DRUMS.values())
        assert len(keys) == len(set(keys)), "Duplicate keys found in KEYMAP_DRUMS"

    def test_all_notes_are_unique(self):
        """All MIDI notes in KEYMAP_DRUMS should be unique."""
        notes = list(KEYMAP_DRUMS.keys())
        assert len(notes) == len(set(notes)), "Duplicate notes found in KEYMAP_DRUMS"

    def test_keymap_keys_are_strings(self):
        """All values in KEYMAP_DRUMS should be strings."""
        for key_value in KEYMAP_DRUMS.values():
            assert isinstance(
                key_value, str
            ), f"Key value '{key_value}' is not a string"

    def test_keymap_notes_are_integers(self):
        """All keys in KEYMAP_DRUMS should be integers."""
        for note_key in KEYMAP_DRUMS.keys():
            assert isinstance(note_key, int), f"Note key '{note_key}' is not an int"

    def test_keymap_uses_expected_keys(self):
        """KEYMAP_DRUMS should use only Y, U, I, O, H, J, K, L keys."""
        expected_keys = {"y", "u", "i", "o", "h", "j", "k", "l"}
        actual_keys = set(KEYMAP_DRUMS.values())
        assert actual_keys == expected_keys, (
            f"Expected keys {expected_keys}, got {actual_keys}"
        )


class TestDrumLayout:
    """Test drum layout matches documentation (top row YUIO, bottom row HJKL)."""

    def test_top_row_notes(self):
        """Notes 60-63 should map to top row keys Y, U, I, O."""
        assert midi_note_to_key(60) == "y"
        assert midi_note_to_key(61) == "u"
        assert midi_note_to_key(62) == "i"
        assert midi_note_to_key(63) == "o"

    def test_bottom_row_notes(self):
        """Notes 64-67 should map to bottom row keys H, J, K, L."""
        assert midi_note_to_key(64) == "h"
        assert midi_note_to_key(65) == "j"
        assert midi_note_to_key(66) == "k"
        assert midi_note_to_key(67) == "l"
