# Xylophone (8-key) Layout Design

**Date:** 2026-02-12
**Status:** Approved
**Feature:** Add Xylophone (8-key) natural note layout for Heartopia

## Overview

Add a new 8-key xylophone instrument layout to Maestro that maps natural notes (C major scale) to the home row keyboard keys A-K. This provides a simple, melodic 8-key instrument distinct from the existing chromatic drums layout.

## Requirements

- Display as "Xylophone (8-key)" in the GUI dropdown
- Map 8 natural notes (DO, RE, MI, FA, SOL, LA, SI, DO) to keys A, S, D, F, G, H, J, K
- Skip notes outside the natural scale range (no transposition)
- Follow the same architecture pattern as the drums keymap
- Comprehensive test coverage

## Architecture

### Key Specifications

| MIDI Note | Note Name | Keyboard Key | Solfège |
|-----------|-----------|--------------|---------|
| 60 | C4 | A | DO |
| 62 | D4 | S | RE |
| 64 | E4 | D | MI |
| 65 | F4 | F | FA |
| 67 | G4 | G | SOL |
| 69 | A4 | H | LA |
| 71 | B4 | J | SI |
| 72 | C5 | K | DO (octave) |

**Design Decisions:**
- Natural notes only (no sharps/flats) - matches xylophone instrument nature
- No transpose support - skip out-of-range notes (consistent with drums)
- Home row keys for ergonomic playing
- MIDI 60-72 range covers one octave of natural notes

## Implementation

### File 1: `src/maestro/keymap_xylophone.py`

New keymap module following drums pattern:

```python
"""Xylophone keymap for Heartopia 8-key xylophone.

Maps MIDI notes 60, 62, 64, 65, 67, 69, 71, 72 (C major scale, natural notes only)
to keyboard keys A, S, D, F, G, H, J, K.
"""

# MIDI note range (non-contiguous - natural notes only)
MIN_NOTE = 60  # C4 (DO)
MAX_NOTE = 72  # C5 (DO - octave higher)

# Natural notes mapping (C major scale)
KEYMAP_XYLOPHONE = {
    60: "a",  # C4 - DO
    62: "s",  # D4 - RE
    64: "d",  # E4 - MI
    65: "f",  # F4 - FA
    67: "g",  # G4 - SOL
    69: "h",  # A4 - LA
    71: "j",  # B4 - SI
    72: "k",  # C5 - DO (octave higher)
}


def midi_note_to_key(
    note: int,
    transpose: bool = False,  # Not used for xylophone
) -> str | None:
    """Convert MIDI note to keyboard key for xylophone.

    Args:
        note: MIDI note number (0-127)
        transpose: Not used (xylophone doesn't transpose)

    Returns:
        String key character, or None if note is outside natural scale
    """
    return KEYMAP_XYLOPHONE.get(note)
```

**Lines:** ~40 (similar to keymap_drums.py at 41 lines)

### File 2: `src/maestro/key_layout.py`

Add enum value:

```python
class KeyLayout(Enum):
    KEYS_22 = "22-key (Full)"
    KEYS_15_DOUBLE = "15-key (Double Row)"
    KEYS_15_TRIPLE = "15-key (Triple Row)"
    DRUMS = "Drums (8-key)"
    XYLOPHONE = "Xylophone (8-key)"  # NEW
```

**Change:** +1 line

### File 3: `src/maestro/player.py`

**Import (add to existing imports around line 26-31):**
```python
from maestro.keymap_xylophone import midi_note_to_key as midi_note_to_key_xylophone
```

**Dispatch logic (add to `_midi_note_to_key` method after DRUMS check):**
```python
elif self._key_layout == KeyLayout.XYLOPHONE:
    key = midi_note_to_key_xylophone(midi_note, transpose=False)
```

**Changes:** +1 import line, +2 lines in dispatch logic

### File 4: `src/maestro/config.py`

Update validation list (around line 83-87):

```python
valid_layouts = [
    "22-key (Full)",
    "15-key (Double Row)",
    "15-key (Triple Row)",
    "Drums (8-key)",
    "Xylophone (8-key)"  # NEW
]
```

**Change:** +1 line in list

### File 5: `tests/test_keymap_xylophone.py`

New comprehensive test file following drums test pattern:

**Test Classes:**

1. **TestNoteMappings** - Parameterized test for all 8 notes
   - Verify MIDI 60→a, 62→s, 64→d, 65→f, 67→g, 69→h, 71→j, 72→k

2. **TestConstants** - MIN_NOTE, MAX_NOTE validation
   - MIN_NOTE == 60
   - MAX_NOTE == 72

3. **TestBoundaries** - Edge cases
   - MIN (60) returns "a"
   - MAX (72) returns "k"
   - Below MIN (59) returns None

4. **TestTranspose** - Verify transpose parameter ignored
   - transpose=True has no effect
   - transpose=False works normally

5. **TestOutOfRange** - Sharp notes and gaps return None
   - MIDI 61 (C#) returns None
   - MIDI 63 (D#) returns None
   - MIDI 66 (F#) returns None
   - MIDI 68 (G#) returns None
   - MIDI 70 (A#) returns None
   - MIDI 48 (far below) returns None
   - MIDI 96 (far above) returns None

**Expected test count:** ~19 tests (11 test methods with 1 parameterized)

**Lines:** ~90 (similar to test_keymap_drums.py at 87 lines)

## Integration

### GUI

No changes needed! The GUI automatically:
- Reads all `KeyLayout` enum values for the dropdown
- Displays "Xylophone (8-key)" in the layout selection
- Persists selection to config

### Config Validation

Config validation automatically:
- Accepts "Xylophone (8-key)" as valid layout
- Resets to default if invalid value detected
- Saves/loads between sessions

### Player

Player dispatch automatically:
- Routes xylophone layout to correct keymap function
- Disables transpose (passes `transpose=False`)
- Skips sharp notes and out-of-range notes

## Testing Strategy

### Unit Tests

All tests in `tests/test_keymap_xylophone.py`:

- ✅ All 8 natural note mappings correct
- ✅ Constants (MIN_NOTE, MAX_NOTE) correct
- ✅ Boundary validation (min, max, below min)
- ✅ Transpose parameter ignored
- ✅ Sharp notes return None (61, 63, 66, 68, 70)
- ✅ Out-of-range notes return None

### Integration Tests

No new integration tests needed - existing tests in `test_main.py` and `test_player.py` already cover:
- Layout selection from config
- Player dispatch to correct keymap
- GUI dropdown population

### Manual Testing

1. Select "Xylophone (8-key)" from layout dropdown
2. Load a simple C major scale MIDI file
3. Verify keys A-K play correctly
4. Load MIDI with sharps - verify they're skipped
5. Verify setting persists across restarts

## Success Criteria

- ✅ All tests pass (expected +19 tests, total ~351 tests)
- ✅ Xylophone appears in GUI dropdown
- ✅ Natural notes (60, 62, 64, 65, 67, 69, 71, 72) map correctly to A-K
- ✅ Sharp notes and out-of-range notes are skipped
- ✅ No transpose behavior (consistent with drums)
- ✅ Ruff and mypy checks pass
- ✅ Layout selection persists to config

## Files Modified Summary

| File | Type | Lines Changed |
|------|------|---------------|
| `src/maestro/keymap_xylophone.py` | New | +40 |
| `src/maestro/key_layout.py` | Modify | +1 |
| `src/maestro/player.py` | Modify | +3 |
| `src/maestro/config.py` | Modify | +1 |
| `tests/test_keymap_xylophone.py` | New | +90 |
| **Total** | | **+135 lines** |

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| MIDI files with sharps sound incomplete | Documented behavior - xylophone is natural notes only |
| User confusion between drums/xylophone | Clear naming: "Drums (8-key)" vs "Xylophone (8-key)" |
| Limited 8-key range | Expected - xylophone is a simple instrument |

## Future Enhancements (Not in Scope)

- Optional transpose for xylophone (if user feedback requests it)
- Extended xylophone layout (12-15 keys with sharps)
- Custom keymap editor for user-defined layouts

## References

- Existing drums implementation: `src/maestro/keymap_drums.py`
- Existing drums tests: `tests/test_keymap_drums.py`
- KeyLayout enum: `src/maestro/key_layout.py`
- Player dispatch: `src/maestro/player.py` lines 236-262
