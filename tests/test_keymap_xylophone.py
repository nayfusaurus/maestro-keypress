"""Tests for Heartopia 8-key xylophone keymap."""

from maestro.keymap_xylophone import midi_note_to_key


class TestXylophoneMappings:
    """Smoke-check mappings, boundaries, sharps, and transpose."""

    def test_boundary_notes(self):
        assert midi_note_to_key(60) == ("a", 60)  # first
        assert midi_note_to_key(72) == ("k", 72)  # last

    def test_sharp_notes_return_none(self):
        assert midi_note_to_key(61) is None
        assert midi_note_to_key(66) is None

    def test_out_of_range_returns_none(self):
        assert midi_note_to_key(59) is None
        assert midi_note_to_key(73) is None

    def test_transpose_ignored(self):
        """Transpose param has no effect on xylophone."""
        assert midi_note_to_key(59, transpose=True) is None
        assert midi_note_to_key(60, transpose=True) == ("a", 60)
