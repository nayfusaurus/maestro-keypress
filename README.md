# Maestro - Heartopia Music Player

Auto-play MIDI songs on Heartopia's in-game piano by simulating keyboard presses.

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd maestro-keypress
uv sync
```

## Usage

1. Drop `.mid` files into the `songs/` folder
2. Run: `uv run maestro`
3. Use hotkeys:
   - **F1** - Open song picker
   - **F2** - Play/Pause
   - **F3** - Stop playback
   - **Ctrl+C** - Exit

After selecting a song, you have 3 seconds to switch to Heartopia before playback starts.

## Heartopia Key Mapping

The app maps MIDI notes to Heartopia's 3-octave piano:

| Octave | DO | RE | MI | FA | SOL | LA | SI |
|--------|----|----|----|----|-----|----|----|
| High   | Q  | W  | E  | R  | T   | Y  | U  |
| Mid    | Z  | X  | C  | V  | B   | N  | M  |
| Low    | L  | ;  | /  | O  | P   | [  | ]  |

Notes outside this range are automatically transposed.

## Development

Run tests:

```bash
uv run pytest -v
```

## Project Structure

```text
maestro-keypress/
├── src/maestro/
│   ├── __init__.py    # Entry point
│   ├── main.py        # App coordinator + hotkeys
│   ├── player.py      # Playback engine
│   ├── parser.py      # MIDI file parsing
│   ├── keymap.py      # Heartopia key mapping
│   └── gui.py         # Tkinter song picker
├── tests/             # Test suite
├── songs/             # MIDI files go here
└── pyproject.toml     # Project config
```

## License

MIT
