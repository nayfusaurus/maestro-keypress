# Where Winds Meet Support - Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add Where Winds Meet (WWM) game support alongside existing Heartopia mode.

**Architecture:** Game-agnostic player with swappable keymaps. GUI dropdown to select game mode. WWM uses modifier keys (Shift for sharps) instead of dedicated black keys.

**Tech Stack:** Python, pynput (keyboard simulation with modifiers), tkinter

---

## Summary of Decisions

1. **Game selection**: Manual toggle dropdown in GUI
2. **Sharps/flats**: Always use sharps (Shift+key)
3. **WWM octave range**: C4-B6 (MIDI 60-83), transpose everything else

---

## Architecture

```
src/maestro/
├── keymap.py              # Existing Heartopia mapping (unchanged API)
├── keymap_wwm.py          # NEW: Where Winds Meet mapping
├── game_mode.py           # NEW: GameMode enum
├── player.py              # Updated to handle modifiers
├── gui.py                 # Add game mode dropdown
└── main.py                # Wire up game mode callback
```

---

## Where Winds Meet Keymap

WWM uses numbered notation (1-7 = Do-Re-Mi-Fa-Sol-La-Si) with Shift for sharps.

**Natural notes map directly:**
- C (0) → base key
- D (2) → base key
- E (4) → base key
- F (5) → base key
- G (7) → base key
- A (9) → base key
- B (11) → base key

**Sharp notes use Shift modifier:**
- C# (1) → Shift + C key
- D# (3) → Shift + D key
- F# (6) → Shift + F key
- G# (8) → Shift + G key
- A# (10) → Shift + A key

**Key layout by octave:**

| Pitch  | 1(C) | 2(D) | 3(E) | 4(F) | 5(G) | 6(A) | 7(B) |
|--------|------|------|------|------|------|------|------|
| High   | Q    | W    | E    | R    | T    | Y    | U    |
| Medium | A    | S    | D    | F    | G    | H    | J    |
| Low    | Z    | X    | C    | V    | B    | N    | M    |

**MIDI range:** 48-83 (C3-B5) maps to 3 octaves. Notes outside get transposed.

---

## Implementation Tasks

### Task 1: Create GameMode enum

**Files:**
- Create: `src/maestro/game_mode.py`

```python
from enum import Enum

class GameMode(Enum):
    HEARTOPIA = "Heartopia"
    WHERE_WINDS_MEET = "Where Winds Meet"
```

### Task 2: Create WWM keymap

**Files:**
- Create: `src/maestro/keymap_wwm.py`
- Create: `tests/test_keymap_wwm.py`

The function returns `tuple[str, Key | None]` where second element is modifier.

```python
def midi_note_to_key_wwm(midi_note: int) -> tuple[str, Key | None]:
    """Convert MIDI note to WWM key + optional Shift modifier."""
```

### Task 3: Update Player to handle modifiers

**Files:**
- Modify: `src/maestro/player.py`

Add `game_mode` property and update `_press_key()`:

```python
def _press_key(self, key: str, modifier: Key | None = None) -> None:
    if modifier:
        self.keyboard.press(modifier)
    self.keyboard.press(key)
    time.sleep(0.02)
    self.keyboard.release(key)
    if modifier:
        self.keyboard.release(modifier)
```

### Task 4: Add game mode dropdown to GUI

**Files:**
- Modify: `src/maestro/gui.py`

Add dropdown at top of window, call `on_game_change` callback when changed.

### Task 5: Wire up game mode in main.py

**Files:**
- Modify: `src/maestro/main.py`

Pass game mode callback to GUI, update player's game_mode when changed.

### Task 6: Update documentation

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`

Add WWM support section with key mapping table.

---

## Testing

- Test WWM keymap for natural notes (C, D, E, F, G, A, B)
- Test WWM keymap for sharp notes (C#, D#, F#, G#, A#)
- Test transposition for notes outside range
- Test modifier key pressing in player (manual testing)
