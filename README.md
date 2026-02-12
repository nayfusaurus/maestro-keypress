# Maestro - MIDI Piano Player

Auto-play MIDI songs on in-game pianos by simulating keyboard presses. Supports:

- **Heartopia** (22-key, 15-key Double Row, 15-key Triple Row, Drums 8-key)
- **Where Winds Meet**

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url>
cd maestro-keypress
uv venv
uv sync
```

## Usage

1. Drop `.mid` or `.midi` files into the `songs/` folder (or use Browse to select any folder)
2. Run: `uv run maestro`
3. The song picker opens automatically
4. Select a song and click Play (or double-click)
5. The window auto-minimizes and playback starts after a 3-second countdown

**Hotkeys (configurable in Settings):**

- **F2** - Play
- **F3** - Stop playback
- **Escape** - Emergency stop (always active)
- **Ctrl+C** - Exit

## Game Selection

Use the dropdown in the song picker to switch between games:

- **Heartopia** - Default. Uses pynput for keyboard simulation. Supports 4 key layouts:
  - **22-key (Full)** - 3 octaves (C3-C6) with sharps
  - **15-key (Double Row)** - 2 octaves (C4-C6), naturals only, keys A-J + Q-I
  - **15-key (Triple Row)** - 2 octaves (C4-C6), naturals only, keys Y-P / H-; / N-/
  - **Conga/Cajon (8-key)** - Chromatic C4-G4 (MIDI 60-67), keys YUIO/HJKL, transpose/sharp disabled
- **Where Winds Meet** - Uses Shift modifier for sharps. Uses DirectInput (pydirectinput) for keyboard simulation.

The game mode affects which keyboard layout and input method is used for playback.

**Song Picker Features:**

- Search bar to filter songs
- Progress bar with time display
- Now Playing panel with current song name
- Browse button to change folders
- Speed slider (0.25x - 1.5x)
- Visual countdown before playback
- Error display in status bar
- MIDI validation with color-coded status (green/red/gray), incremental with mtime caching
- Song info display (duration, BPM, note count)
- Note compatibility percentage for current layout
- Favorites with star toggle (sorted first)
- Recently played tracking
- Song finished notification (title flash + green status + window restore)
- Sharp handling setting (skip or snap to nearest natural)
- Hotkey remapping (press-to-bind in Settings) with conflict detection
- Auto-minimize on play
- Optional piano roll preview panel
- Settings persist between sessions
- Closing the window exits the app

## Heartopia Key Mapping

### 22-key (Full) Layout

Maps MIDI notes to Heartopia's piano (3 octaves, C3-C6):

| Octave | DO  | DO# | RE  | RE# | MI  | FA  | FA# | SOL | SOL# | LA  | LA# | SI  |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|------|-----|-----|-----|
| High   | Q   | 2   | W   | 3   | E   | R   | 5   | T   | 6    | Y   | 7   | U   |
| Mid    | Z   | S   | X   | D   | C   | V   | G   | B   | H    | N   | J   | M   |
| Low    | ,   | L   | .   | ;   | /   | O   | 0   | P   | -    | [   | =   | ]   |

Plus `I` for the highest DO (C6).

### 15-key Layouts

For Heartopia's 15-key piano modes, only natural notes (no sharps) are supported. Sharp notes can be configured to either skip or snap to the nearest natural in Settings.

Out-of-range notes are skipped by default. Enable transpose in Settings to shift them into the playable range.

### Conga/Cajon (8-key) - Heartopia

Maps chromatic MIDI notes to 8 keys (conga drums):

**Top row:** Y (60/C4), U (61/C#4), I (62/D4), O (63/D#4)
**Bottom row:** H (64/E4), J (65/F4), K (66/F#4), L (67/G4)

- **Note range:** MIDI 60-67 (chromatic C4-G4)
- **Out-of-range handling:** Notes outside 60-67 are skipped
- **Transpose/sharp:** Disabled for drums layout (chromatic mapping, no transposition needed)

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

The app requires native Windows to capture global hotkeys (WSL won't work).

### Prerequisites

1. Install [uv](https://docs.astral.sh/uv/):

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

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
uv venv
uv sync
uv add pyinstaller --dev

# Build the exe
uv run pyinstaller Maestro.spec --noconfirm
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

### Quality & Performance Features

- **Event caching:** Built events are cached and reused when only playback speed changes, avoiding expensive re-parsing
- **Incremental validation:** MIDI files validated using mtime caching to skip unchanged files
- **Pinned dependencies:** All dependencies locked to specific versions for reproducibility
- **Code quality:** Linted with ruff and mypy for type safety and code quality
- **Security scanning:** pip-audit checks for known vulnerabilities in dependencies (CI)
- **Release checksums:** SHA256 checksums provided for Windows exe releases
- **Hotkey conflict detection:** Prevents binding the same key to multiple actions
- **Window restore:** Automatically restores window from minimized state when song finishes

## Project Structure

```text
maestro-keypress/
├── src/maestro/
│   ├── __init__.py         # Entry point
│   ├── main.py             # App coordinator + hotkeys + conflict detection
│   ├── player.py           # Event-driven playback engine with caching
│   ├── parser.py           # MIDI parsing with multi-tempo support
│   ├── keymap.py           # Heartopia 22-key mapping
│   ├── keymap_15_double.py # Heartopia 15-key double row mapping
│   ├── keymap_15_triple.py # Heartopia 15-key triple row mapping
│   ├── keymap_drums.py     # Heartopia 8-key drums mapping
│   ├── keymap_wwm.py       # Where Winds Meet mapping
│   ├── key_layout.py       # KeyLayout enum
│   ├── game_mode.py        # Game selection enum
│   ├── gui.py              # Tkinter song picker with incremental validation
│   ├── config.py           # Settings persistence with validation
│   └── logger.py           # Error logging
├── tests/                  # Test suite (385 tests, 2 skipped)
│   ├── test_keymap_drums.py  # Drums keymap tests
│   ├── ...                   # Other test files
├── songs/                  # .mid/.midi files go here
├── pyproject.toml          # Project config with pinned dependencies
└── .github/workflows/      # CI with ruff, mypy, pip-audit
```

## License

MIT
