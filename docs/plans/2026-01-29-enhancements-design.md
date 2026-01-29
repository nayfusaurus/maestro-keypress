# Maestro Enhancements Design

**Date:** 2026-01-29
**Status:** Approved

## Overview

This document outlines 8 enhancements to the Maestro MIDI player application, improving usability, error visibility, and adding visual features.

---

## Enhancement 1: GUI Opens Immediately on Startup

### Current Behavior
- App starts, prints hotkey instructions, waits for F1 to show GUI

### New Behavior
- App starts, prints hotkey instructions, shows GUI immediately
- F1 hotkey removed (GUI always visible)
- F2 = Play only (starts playback if song loaded)
- F3 = Stop

### Files Changed
- `src/maestro/main.py`

---

## Enhancement 2: Remove Pause Functionality

### Rationale
User requested play/stop only, no pause needed.

### Changes
- Remove `PlaybackState.PAUSED` enum value
- Remove `pause()` and `toggle_pause()` methods from Player
- Remove pause event logic from playback loop
- Remove Pause button from GUI
- Remove `on_pause` callback from SongPicker

### Simplified State Machine
```
STOPPED <--> PLAYING
```

### Files Changed
- `src/maestro/player.py`
- `src/maestro/gui.py`
- `src/maestro/main.py`

---

## Enhancement 3: Settings Persistence (AppData)

### Config Location
- Windows: `%APPDATA%/Maestro/config.json`
- Linux/Mac: `~/.maestro/config.json`

### Config Structure
```json
{
  "last_songs_folder": "C:/Users/Yan/Music/midi",
  "game_mode": "Heartopia",
  "speed": 1.0,
  "preview_lookahead": 5
}
```

### New Module: `src/maestro/config.py`
```python
def get_config_dir() -> Path:
    """Return platform-appropriate config directory."""

def load_config() -> dict:
    """Load config from JSON, return defaults if missing."""

def save_config(settings: dict) -> None:
    """Save settings to JSON file."""
```

### Save Triggers
- Folder changed via Browse button
- Game mode changed
- Speed slider changed
- Preview lookahead changed
- Window closed (final save)

### Files Changed
- **New:** `src/maestro/config.py`
- `src/maestro/main.py`
- `src/maestro/gui.py`

---

## Enhancement 4: Error Logging & Handling

### Log Location
- Windows: `%APPDATA%/Maestro/maestro.log`
- Linux/Mac: `~/.maestro/maestro.log`

### New Module: `src/maestro/logger.py`
- Uses Python's `logging` module
- Rotating file handler (1MB max, 3 backups)
- Format: `2026-01-29 10:30:45 [ERROR] Message`

### Errors Captured

| Source | Error Type | GUI Display |
|--------|------------|-------------|
| parser.py | Invalid MIDI file | "Error: Invalid MIDI file" |
| parser.py | File not found | "Error: File not found" |
| player.py | Keypress failure | "Error: Key simulation failed" |
| General | Unexpected errors | "Error: See log for details" |

### GUI Changes
- Status label shows last error in red text
- Add "Open Log" button next to status area
- Button opens log file in default text editor

### Files Changed
- **New:** `src/maestro/logger.py`
- `src/maestro/player.py` (replace bare except)
- `src/maestro/parser.py` (add logging)
- `src/maestro/gui.py` (error display, Open Log button)
- `src/maestro/main.py` (initialize logger)

---

## Enhancement 5: Speed Range Alignment

### Current Mismatch
- `player.py` clamps to 0.1 - 2.0
- GUI slider allows 0.25 - 1.5

### Fix
Align backend to match GUI:
```python
# player.py line 76
self._speed = max(0.25, min(1.5, value))
```

### Files Changed
- `src/maestro/player.py`

---

## Enhancement 6: Countdown Timer

### Current Behavior
- Console prints "Playing 'song' in 3 seconds..."
- No visual feedback in GUI

### New Behavior
- Status label shows countdown: "Starting in 3..." → "Starting in 2..." → "Starting in 1..." → "Playing"
- Countdown happens in existing delayed_play thread
- GUI updates via existing 200ms polling

### Implementation
- Add `_countdown` property to Maestro class
- Update `_get_state_string()` to return countdown text when counting
- Delayed play thread updates countdown value each second

### Files Changed
- `src/maestro/main.py`

---

## Enhancement 7: Piano Roll Note Preview

### Visual Design
```
┌─ Note Preview ─────────────────────────────────┐
│  ░░░▓▓░░░░▓▓▓░░░▓░░░░░░░░░░░░░│← playhead     │
│  ░▓▓░░░▓▓░░░░░▓▓░░░░░░░░░░░░░░│               │
│  ▓░░░░░░░▓▓░░░░░░▓░░░░░░░░░░░░│               │
│  [2s ▼]                                        │
└────────────────────────────────────────────────┘
```

### Components
- Tkinter `Canvas` widget for drawing
- Vertical axis: Note pitch (higher notes at top)
- Horizontal axis: Time (left = now, right = future)
- Notes drawn as colored rectangles
- Playhead line on left edge
- Dropdown to select lookahead: 2s / 5s / 10s

### Data Flow
1. Player exposes `get_upcoming_notes(lookahead_seconds)` method
2. GUI calls this every 200ms during update cycle
3. Canvas redraws with current notes

### Player Method
```python
def get_upcoming_notes(self, lookahead: float) -> list[Note]:
    """Return notes within lookahead seconds from current position."""
```

### GUI Changes
- Add LabelFrame "Note Preview" below "Now Playing"
- Add Canvas widget (width: full, height: ~100px)
- Add lookahead dropdown (2s / 5s / 10s)
- Window height increased from 550px to ~700px

### Config Integration
- `preview_lookahead` saved to config.json

### Files Changed
- `src/maestro/player.py`
- `src/maestro/gui.py`

---

## Enhancement 8: Remove Unused Import

### Change
Remove unused `import sys` from `src/maestro/main.py` line 6.

### Files Changed
- `src/maestro/main.py`

---

## Summary of All Changes

| File | Changes |
|------|---------|
| **New:** `src/maestro/config.py` | Settings persistence module |
| **New:** `src/maestro/logger.py` | Logging setup module |
| `src/maestro/main.py` | Remove sys import, auto-show GUI, countdown, F2=play only |
| `src/maestro/player.py` | Remove pause, fix speed range, add get_upcoming_notes, error logging |
| `src/maestro/gui.py` | Remove pause button, add Open Log, add piano roll, save settings |
| `src/maestro/parser.py` | Add error logging |

## Window Layout (Updated)

```
┌─ Maestro - Song Picker ────────────────────────┐
│ Folder: [path]                      [Browse...] │
│ Game: [Heartopia ▼]                             │
│ Speed: [━━━━━●━━━] 1.00x                        │
│ Search: [________________]                      │
│                                                 │
│ Songs:                                          │
│ ┌─────────────────────────────────────────────┐ │
│ │ Song 1                                    ▲ │ │
│ │ Song 2                                    █ │ │
│ │ Song 3                                    █ │ │
│ │ Song 4                                    ▼ │ │
│ └─────────────────────────────────────────────┘ │
│ [Play] [Stop] [Refresh]                         │
│                                                 │
│ ┌─ Now Playing ─────────────────────────────┐   │
│ │ Song Name                                 │   │
│ │ [████████░░░░░░░░░░░░] 1:23 / 3:45       │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ ┌─ Note Preview ────────────────────────────┐   │
│ │ ░░░▓▓░░░░▓▓▓░░░▓░░░░░░░░░░░░░            │   │
│ │ ░▓▓░░░▓▓░░░░░▓▓░░░░░░░░░░░░░░            │   │
│ │ ▓░░░░░░░▓▓░░░░░░▓░░░░░░░░░░░░            │   │
│ │ [5s ▼]                                    │   │
│ └───────────────────────────────────────────┘   │
│                                                 │
│ Status: Playing          Key: C   [Open Log]    │
└─────────────────────────────────────────────────┘
```

Window size: 400x700px
