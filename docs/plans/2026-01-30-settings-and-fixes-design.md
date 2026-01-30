# Settings Page and Fixes Design

## Overview

Add a settings page with transposition and preview panel toggles, improve error display visibility, and fix the duration calculation bug.

## Changes

### 1. Menu Bar

Add a menu bar to the main window:

- **File menu:**
  - Open Log — opens the log file (existing functionality)
  - Settings — opens settings dialog (new)
  - Exit — closes the application

- **Help menu:**
  - About — shows about dialog (existing functionality)

Remove "About" and "Open Log" buttons from the status bar. Status bar will only contain the status label (left) and key display (right).

### 2. Settings Dialog

Modal dialog centered over main window (similar to existing About dialog).

**Title:** "Settings"

**Contents:**
- Checkbox: "Transpose notes to playable range"
  - Unchecked (default): Notes outside playable range are skipped
  - Checked: Notes outside range are transposed into range
- Checkbox: "Show note preview panel"
  - Unchecked (default): Note Preview panel is hidden
  - Checked: Note Preview panel is visible

**Buttons:** Close button at bottom

**Persistence:** Both settings saved to config.json alongside existing settings.

### 3. Error Display

Add a dedicated error label above the "Now Playing" panel.

**Appearance:**
- Red text, larger than status bar text for visibility
- Only visible when there's an error to display

**Behavior:**
- Shows when MIDI file fails to load or parse
- Clears when user selects a new song or successfully plays a file
- Logging to file continues for detailed debugging

### 4. Duration Fix

**Problem:** Timer shows 100% complete when the last note starts, not when it finishes playing.

**Current code** (player.py):
```python
@property
def duration(self) -> float:
    if not self._notes:
        return 0.0
    return self._notes[-1].time
```

**Fixed code:**
```python
@property
def duration(self) -> float:
    if not self._notes:
        return 0.0
    last_note = self._notes[-1]
    return last_note.time + last_note.duration
```

### 5. Keymap Changes (Transposition Toggle)

Modify both keymap functions to support optional transposition:

**keymap.py** — `midi_note_to_key(midi_note, transpose=False)`
- When `transpose=False`: Return `None` for notes outside MIDI 36-84
- When `transpose=True`: Transpose notes into range (current behavior)

**keymap_wwm.py** — `midi_note_to_key_wwm(midi_note, transpose=False)`
- When `transpose=False`: Return `None` for notes outside MIDI 48-83
- When `transpose=True`: Transpose notes into range (current behavior)

**Player changes:**
- Add `transpose` property to Player class
- Pass transpose setting to keymap functions
- Skip notes when keymap returns `None`

## Files to Modify

| File | Changes |
|------|---------|
| `src/maestro/gui.py` | Menu bar, settings dialog, error label, hide preview panel by default |
| `src/maestro/player.py` | Duration fix, transpose property |
| `src/maestro/keymap.py` | Add transpose parameter |
| `src/maestro/keymap_wwm.py` | Add transpose parameter |
| `src/maestro/config.py` | Add transpose and show_preview settings |
| `src/maestro/main.py` | Wire up new settings between GUI and Player |
| `tests/test_keymap.py` | Test transpose parameter |
| `tests/test_keymap_wwm.py` | Test transpose parameter |
| `tests/test_player.py` | Test duration fix, transpose setting |
| `tests/test_config.py` | Test new config keys |

## Config Schema

New keys added to config.json:

```json
{
  "songs_folder": "/path/to/songs",
  "game_mode": "Heartopia",
  "speed": 1.0,
  "lookahead": 5,
  "transpose": false,
  "show_preview": false
}
```

## Default Behavior Changes

| Setting | Old Default | New Default |
|---------|-------------|-------------|
| Transposition | Always on | Off (notes skipped) |
| Note Preview panel | Always visible | Hidden |
