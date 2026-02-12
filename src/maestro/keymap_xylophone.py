"""Xylophone keymap for Heartopia 8-key instrument.

Maps natural notes only (C major scale) to keyboard keys A-K.
MIDI notes: 60 (C4), 62 (D4), 64 (E4), 65 (F4), 67 (G4), 69 (A4), 71 (B4), 72 (C5)
Keys: A, S, D, F, G, H, J, K
"""

# MIDI note range
MIN_NOTE = 60  # C4 (DO)
MAX_NOTE = 72  # C5 (DO)

# Natural notes only (C major scale)
# Maps to string keys (not KeyCode objects) for consistency with other keymaps
KEYMAP_XYLOPHONE = {
    60: "a",  # C4 - DO
    62: "s",  # D4 - RE
    64: "d",  # E4 - MI
    65: "f",  # F4 - FA
    67: "g",  # G4 - SOL
    69: "h",  # A4 - LA
    71: "j",  # B4 - SI
    72: "k",  # C5 - DO
}


def midi_note_to_key(
    note: int,
    transpose: bool = False,  # Not used for xylophone, included for API consistency
) -> str | None:
    """Convert MIDI note to keyboard key for xylophone.

    Args:
        note: MIDI note number (0-127)
        transpose: Not used for xylophone (xylophone doesn't transpose)

    Returns:
        String key character for the xylophone key, or None if note is outside range
        or is a sharp/flat note (only natural notes are mapped)
    """
    # Xylophone uses natural notes only (C major scale), no transposition
    return KEYMAP_XYLOPHONE.get(note)
