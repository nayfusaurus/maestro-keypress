# Maestro - MIDI Piano Player

Auto-play MIDI songs on in-game pianos by simulating keyboard presses. Supports:

- **Heartopia**
- **Where Winds Meet**

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd maestro-keypress
uv sync
```

## Usage

1. Drop `.mid` files into the `songs/` folder (or use Browse to select any folder)
2. Run: `uv run maestro`
3. Press **F1** to open the song picker
4. Select a song and click Play (or double-click)
5. Switch to Heartopia within 3 seconds - playback starts automatically

**Hotkeys:**

- **F1** - Open song picker
- **F2** - Play/Pause
- **F3** - Stop playback
- **Ctrl+C** - Exit

## Game Selection

Use the dropdown in the song picker to switch between games:

- **Heartopia** - Default. Uses dedicated black keys for sharps.
- **Where Winds Meet** - Uses Shift modifier for sharps.

The game mode affects which keyboard layout is used for playback.

**Song Picker Features:**

- Search bar to filter songs
- Progress bar with time display
- Now Playing panel with current song name
- Browse button to change folders
- Closing the window exits the app

## Heartopia Key Mapping

The app maps MIDI notes to Heartopia's piano (3 octaves + 2 extended notes):

| Octave | DO  | DO# | RE  | RE# | MI  | FA  | FA# | SOL | SOL# | LA  | LA# | SI  |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|------|-----|-----|-----|
| High   | Q   | 2   | W   | 3   | E   | R   | 5   | T   | 6    | Y   | 7   | U   |
| Mid    | Z   | S   | X   | D   | C   | V   | G   | B   | H    | N   | J   | M   |
| Low    | L   | .   | ;   | '   | /   | O   | 0   | P   | -    | [   | =   | ]   |

Extended: `,` (lowest DO) and `I` (highest DO)

Notes outside this range are automatically transposed.

## Where Winds Meet Key Mapping

WWM uses numbered notation (1-7 = Do-Ti) with Shift for sharps:

| Octave | 1(C) | 2(D) | 3(E) | 4(F) | 5(G) | 6(A) | 7(B) |
|--------|------|------|------|------|------|------|------|
| High   | Q    | W    | E    | R    | T    | Y    | U    |
| Medium | A    | S    | D    | F    | G    | H    | J    |
| Low    | Z    | X    | C    | V    | B    | N    | M    |

Sharp notes: Hold Shift + the natural note key (e.g., C# = Shift+C key).

Notes outside MIDI 48-83 are automatically transposed.

## Building for Windows

The app requires native Windows Python to capture global hotkeys (WSL won't work).

### Prerequisites

1. Install Python 3.11+ from [python.org](https://www.python.org/downloads/)
   - Check "Add Python to PATH" during installation
2. Open PowerShell or Command Prompt

### Option 1: Using build.bat (Recommended)

Simply double-click `build.bat` or run it from the command line:

```powershell
.\build.bat
```

This automatically installs dependencies and builds the exe.

### Option 2: Manual Build

```powershell
# Install dependencies
pip install mido pynput pyinstaller

# Build the exe
pyinstaller Maestro.spec --noconfirm
```

### Output

The exe will be at `dist/Maestro.exe`. You can:

- Run it directly by double-clicking
- Move it anywhere - it's fully standalone
- Create a shortcut on your desktop

### Troubleshooting

- **"Python not found"**: Reinstall Python with "Add to PATH" checked
- **Build fails**: Make sure you're using Windows Python, not WSL
- **Hotkeys don't work**: Run as administrator if needed

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
│   ├── keymap_wwm.py  # Where Winds Meet key mapping
│   ├── game_mode.py   # Game selection enum
│   └── gui.py         # Tkinter song picker
├── tests/             # Test suite
├── songs/             # MIDI files go here
└── pyproject.toml     # Project config
```

## License

MIT
