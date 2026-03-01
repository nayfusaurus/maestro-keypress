"""Tests for Heartopia 8-key drum keymap."""

from maestro.keymap_drums import midi_note_to_key


class TestDrumMappings:
    """Smoke-check mappings, boundaries, and transpose."""

    def test_boundary_notes(self):
        assert midi_note_to_key(60) == "y"  # first
        assert midi_note_to_key(67) == "l"  # last

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key(59) is None
        assert midi_note_to_key(68) is None

    def test_transpose_ignored(self):
        """Transpose param has no effect on drums."""
        assert midi_note_to_key(59, transpose=True) is None
        assert midi_note_to_key(60, transpose=True) == "y"
