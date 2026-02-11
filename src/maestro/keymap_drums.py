"""Drum keymap for Heartopia 8-key drums.

Maps MIDI notes 60-67 (chromatic) to keyboard keys YUIO/HJKL.
Top row: Y, U, I, O (notes 60, 61, 62, 63)
Bottom row: H, J, K, L (notes 64, 65, 66, 67)
"""

from pynput.keyboard import Key, KeyCode

# MIDI note range
MIN_NOTE = 60  # C4
MAX_NOTE = 67  # G4

# Full chromatic mapping (C4-G4)
KEYMAP_DRUMS = {
    60: KeyCode.from_char("y"),  # C4 - Low Conga (open)
    61: KeyCode.from_char("u"),  # C#4 - Low Conga (muted)
    62: KeyCode.from_char("i"),  # D4 - Conga (open)
    63: KeyCode.from_char("o"),  # D#4 - Conga (muted/slap)
    64: KeyCode.from_char("h"),  # E4 - High Conga (open)
    65: KeyCode.from_char("j"),  # F4 - High Timbale
    66: KeyCode.from_char("k"),  # F#4 - Low Timbale
    67: KeyCode.from_char("l"),  # G4 - High Agogo
}


def midi_note_to_key(
    note: int,
    transpose: bool = False,  # Not used for drums, included for API consistency
) -> Key | KeyCode | None:
    """Convert MIDI note to keyboard key for drums.

    Args:
        note: MIDI note number (0-127)
        transpose: Not used for drums (drums don't transpose)

    Returns:
        KeyCode for the drum key, or None if note is outside range
    """
    # Drums are chromatic 60-67, no transposition
    return KEYMAP_DRUMS.get(note)
