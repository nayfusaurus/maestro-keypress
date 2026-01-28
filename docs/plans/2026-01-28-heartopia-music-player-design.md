# Heartopia Music Player (Maestro) - Design Document

## Overview

A Python background app that auto-plays MIDI songs on Heartopia's in-game piano by simulating keyboard presses.

## User Flow

1. Start the app (`uv run maestro`)
2. Press **Alt+N** to open song picker
3. Select a MIDI file from the list
4. Click into Heartopia (2-3 second delay to switch focus)
5. Song plays automatically via simulated keypresses
6. **Alt+M** to pause/resume, **Escape** to stop

## Project Structure

```
maestro-keypress/
├── pyproject.toml      # uv project config
├── songs/              # Drop MIDI files here
└── src/
    └── maestro/
        ├── __init__.py
        ├── main.py     # Entry point, hotkey listener
        ├── gui.py      # Tkinter song picker
        ├── player.py   # MIDI parsing & playback logic
        └── keymap.py   # Heartopia note-to-key mapping
```

## Dependencies

- `mido` - MIDI file parsing
- `pynput` - Global hotkey listening + keyboard simulation
- `tkinter` - GUI (built-in)

## Key Mapping

Heartopia uses a 3-octave piano layout with solfege notation:

| Octave | DO | RE | MI | FA | SOL | LA | SI |
|--------|----|----|----|----|-----|----|----|
| High   | Q  | W  | E  | R  | T   | Y  | U  |
| Mid    | Z  | X  | C  | V  | B   | N  | M  |
| Low    | L  | ;  | /  | O  | P   | [  | ]  |

**Black keys (sharps/flats):**
- High octave: 2, 3, 5, 6, 7
- Mid octave: S, D, G, H, J
- Low octave: ., ', -, =

## MIDI Note Conversion

- MIDI notes are numbered 0-127 (middle C = 60)
- Map a 3-octave range to Heartopia's available keys
- Notes outside the range are transposed to the nearest available octave
- Auto-detect song's note range and shift to fit the 3 octaves

## Hotkeys

| Hotkey | Action |
|--------|--------|
| Alt+N  | Open song picker GUI |
| Alt+M  | Toggle play/pause |
| Escape | Stop playback |

## GUI: Song Picker

- Small Tkinter window (~300x400 pixels)
- Always-on-top
- Lists all `.mid` files from `songs/` folder
- Double-click or Enter to start playing
- Shows playback status: Stopped / Playing / Paused
- Window can be closed without stopping playback

## Playback State Machine

```
[Stopped] ---(select song)---> [Playing]
[Playing] ---(Alt+M)---------> [Paused]
[Paused]  ---(Alt+M)---------> [Playing]
[Playing] ---(Escape)--------> [Stopped]
[Paused]  ---(Escape)--------> [Stopped]
[Playing] ---(song ends)-----> [Stopped]
```

## Playback Details

- Keypresses simulated with timing from MIDI file
- Each note: key down + key up event
- Chords (simultaneous notes) pressed together
- Minimum ~50ms between presses (game registration time)
- 2-3 second delay before playback starts (focus switch time)
- Hotkeys remain responsive during playback

## MIDI Handling

- Multi-track MIDIs: Merge all tracks into one note sequence
- Velocity: Ignored (Heartopia has no velocity support)
- Very fast notes: Minimum 50ms spacing
- Invalid files: Show error in GUI, skip gracefully

## Startup & Shutdown

- Run with `uv run maestro`
- Starts as background process
- Shows notification: "Maestro ready - Alt+N to pick a song"
- Songs list refreshes each time picker opens
- Escape stops playback immediately (no held keys)
- Ctrl+C exits cleanly, releases all hotkeys
