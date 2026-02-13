<div align="center">
  <img src="assets/maestro-logo-clean.png" alt="Maestro" width="500"/>

  <h3>🎹 Automated MIDI Piano Player for Games</h3>
  <p><em>Turn any MIDI file into beautiful in-game piano performances</em></p>

  [![CI](https://github.com/nayfusaurus/maestro-keypress/workflows/CI/badge.svg)](https://github.com/nayfusaurus/maestro-keypress/actions)
  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![GitHub release](https://img.shields.io/github/v/release/nayfusaurus/maestro-keypress)](https://github.com/nayfusaurus/maestro-keypress/releases/latest)
  [![Downloads](https://img.shields.io/github/downloads/nayfusaurus/maestro-keypress/total)](https://github.com/nayfusaurus/maestro-keypress/releases)
  [![Built with Claude](https://img.shields.io/badge/Built%20with-Claude-blueviolet)](https://claude.ai)

  <p>
    <a href="https://github.com/nayfusaurus/maestro-keypress/releases/latest">📦 Download Latest</a> •
    <a href="#-quick-start">🚀 Quick Start</a> •
    <a href="https://github.com/nayfusaurus/maestro-keypress/issues">🐛 Report Issue</a> •
    <a href="https://ko-fi.com/nayfusaurus">💖 Support</a>
  </p>
</div>

---

## ✨ Highlights

- 🎮 **Multi-game support** - Works with Heartopia and Where Winds Meet
- 🎹 **5 keyboard layouts** - 22-key, 15-key double/triple row, Conga/Cajon drums, Xylophone
- ⚡ **Smart MIDI processing** - Auto-validation, transpose, and compatibility checking
- 🎨 **Modern GUI** - Favorites, search, song info, hotkey remapping, and more
- 🎯 **Event-driven playback** - Precise timing with chord support and MIDI duration tracking
- 🔒 **Production-ready** - 362 tests, type-safe with mypy, security-scanned, pinned dependencies
- 🪟 **Windows executable** - Standalone `.exe` for easy distribution

---

## 🚀 Quick Start

### For End Users (Windows)

1. **[Download the latest release](https://github.com/nayfusaurus/maestro-keypress/releases/latest)** (`Maestro.exe`)
2. **Add MIDI files** to a folder (any `.mid` or `.midi` files)
3. **Run `Maestro.exe`** and select your songs folder
4. **Click Play** (or press **F2**) and watch the magic! ✨

The window auto-minimizes and plays your song after a 3-second countdown.

### For Developers

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/nayfusaurus/maestro-keypress.git
cd maestro-keypress
uv sync
uv run maestro
```

---

## ⚙️ Features

### 🎵 Playback
- **Event-driven engine** with precise MIDI timing
- **Chord support** - Multiple keys pressed simultaneously
- **Speed control** - 0.25x to 1.5x playback speed
- **Auto-transpose** - Shift out-of-range notes into playable range
- **Sharp handling** - Skip or snap to nearest natural note (15-key layouts)
- **Multi-tempo support** - Handles MIDI files with tempo changes
- **Window focus detection** - Auto-pauses when game window loses focus (Windows)
- **Stuck key protection** - Ensures all keys are released on exit

### 🖥️ User Interface
- **MIDI validation** - Real-time scan with color-coded status (green/red/gray)
- **Song information** - Duration, BPM, note count, and compatibility percentage
- **Favorites system** - Star your favorite songs (sorted first)
- **Recently played** - Quick access to your last 20 songs
- **Search/filter** - Find songs instantly by name
- **Progress bar** - Visual playback position with time display (M:SS / M:SS)
- **Piano roll preview** - Optional lookahead panel showing upcoming notes
- **Hotkey remapping** - Press-to-bind configuration with conflict detection
- **Settings persistence** - All preferences saved between sessions

### 🎮 Game Support
- **Heartopia** - 5 keyboard layouts (22-key full, 15-key double/triple, drums, xylophone)
- **Where Winds Meet** - DirectInput support with Shift modifier for sharps

### 🛡️ Quality & Performance
- **Event caching** - Reuses built events when only speed changes
- **Incremental validation** - Uses mtime caching to skip unchanged files
- **Type-safe** - Full mypy type checking
- **Security scanned** - pip-audit checks for vulnerabilities (CI)
- **Pinned dependencies** - Locked versions for reproducibility
- **Comprehensive tests** - 362 tests with 99%+ coverage

---

## 🎮 Supported Games

<details>
<summary><b>Heartopia</b> - 5 Keyboard Layouts</summary>

Uses **pynput** for keyboard simulation. Supports 5 distinct key layouts:

### 22-key (Full) Layout
3 octaves (C3-C6) with sharps/flats. Maps MIDI notes to Heartopia's full piano.

| Octave | DO  | DO# | RE  | RE# | MI  | FA  | FA# | SOL | SOL# | LA  | LA# | SI  |
|--------|-----|-----|-----|-----|-----|-----|-----|-----|------|-----|-----|-----|
| High   | Q   | 2   | W   | 3   | E   | R   | 5   | T   | 6    | Y   | 7   | U   |
| Mid    | Z   | S   | X   | D   | C   | V   | G   | B   | H    | N   | J   | M   |
| Low    | ,   | L   | .   | ;   | /   | O   | 0   | P   | -    | [   | =   | ]   |

Plus `I` for the highest DO (C6).

### 15-key Double Row
2 octaves (C4-C6), natural notes only. Keys: **A-J** (bottom) + **Q-I** (top).

Sharp handling: Skip or snap to nearest natural (configurable in Settings).

### 15-key Triple Row
2 octaves (C4-C6), natural notes only. Keys: **Y-P** / **H-;** / **N-/**.

### Conga/Cajon (8-key)
Chromatic mapping for drum sounds. MIDI 60-67 (C4-G4).

**Top row:** Y (60), U (61), I (62), O (63)
**Bottom row:** H (64), J (65), K (66), L (67)

Transpose and sharp handling disabled (chromatic mapping).

### Xylophone (8-key)
Natural notes only (C major scale). MIDI 60-72 (C4-C5).

**Keys:** A (C4), S (D4), D (E4), F (F4), G (G4), H (A4), J (B4), K (C5)

Transpose and sharp handling disabled.

</details>

<details>
<summary><b>Where Winds Meet</b> - Shift Modifier for Sharps</summary>

Uses **DirectInput** (pydirectinput) for keyboard simulation. Numbered notation (1-7 = Do-Ti) with Shift for sharps.

| Octave | 1(C) | 2(D) | 3(E) | 4(F) | 5(G) | 6(A) | 7(B) |
|--------|------|------|------|------|------|------|------|
| High   | Q    | W    | E    | R    | T    | Y    | U    |
| Medium | A    | S    | D    | F    | G    | H    | J    |
| Low    | Z    | X    | C    | V    | B    | N    | M    |

**Sharp notes:** Hold Shift + natural note key (e.g., C# = Shift+C).

Notes outside MIDI 48-83 are automatically transposed.

</details>

---

## 🎹 Usage

### Hotkeys (Configurable)

Default hotkeys (can be remapped in Settings):

| Key       | Action                          |
|-----------|---------------------------------|
| **F2**    | Play selected song              |
| **F3**    | Stop playback                   |
| **Escape** | Emergency stop (always active)  |
| **Ctrl+C** | Exit application                |

### Song Picker Features

1. **Browse** - Select your MIDI files folder
2. **Search** - Filter songs by name in real-time
3. **Validation** - Color-coded status indicators:
   - 🟢 **Green** - Valid, ready to play
   - 🔴 **Red** - Invalid or incompatible
   - ⚪ **Gray** - Pending validation
4. **Song Info** - View duration, BPM, note count, compatibility %
5. **Favorites** - Click the ★ to mark favorites (sorted first)
6. **Speed Slider** - Adjust playback speed (0.25x - 1.5x)
7. **Settings** - Configure transpose, sharp handling, hotkeys, and more

### Workflow

1. Drop `.mid` or `.midi` files into the songs folder
2. Run the app (`uv run maestro` or double-click `Maestro.exe`)
3. Select a song from the list
4. Click Play (or double-click the song)
5. The window auto-minimizes, countdown starts (3 seconds)
6. Maestro plays the song by simulating keyboard presses
7. Window restores when the song finishes

---

## 🏗️ Building for Windows

The app requires **native Windows** to capture global hotkeys (WSL won't work).

### Prerequisites

1. Install [uv](https://docs.astral.sh/uv/):

   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. Open PowerShell or Command Prompt in the project directory

### Option 1: Using build.bat (Recommended)

Simply double-click `build.bat` or run:

```powershell
.\build.bat
```

This automatically installs dependencies and builds the exe.

### Option 2: Manual Build

```powershell
# Install dependencies
uv sync
uv add pyinstaller --dev

# Build the exe
uv run pyinstaller Maestro.spec --noconfirm
```

### Output

The exe will be at `dist/Maestro.exe`. You can:

- Run it directly by double-clicking
- Move it anywhere - it's fully standalone
- Create a desktop shortcut

### Troubleshooting

- **"Python not found"**: Reinstall Python with "Add to PATH" checked
- **Build fails**: Ensure you're using Windows Python, not WSL
- **Hotkeys don't work**: Run as administrator if needed

---

## 🧪 Development

### Running Tests

```bash
uv run pytest -v
```

**Test Suite:** 362 tests, 2 skipped (Windows-only focus detection)

### Code Quality

This project uses:

- **ruff** - Fast Python linter
- **mypy** - Static type checking
- **pip-audit** - Security vulnerability scanning

Enforced in CI on every commit.

### Project Structure

```text
maestro-keypress/
├── src/maestro/
│   ├── __init__.py         # Entry point
│   ├── main.py             # App coordinator + hotkeys
│   ├── player.py           # Event-driven playback engine with caching
│   ├── parser.py           # MIDI parsing with multi-tempo support
│   ├── keymap.py           # Heartopia 22-key mapping
│   ├── keymap_15_double.py # Heartopia 15-key double row
│   ├── keymap_15_triple.py # Heartopia 15-key triple row
│   ├── keymap_drums.py     # Heartopia 8-key drums
│   ├── keymap_xylophone.py # Heartopia 8-key xylophone
│   ├── keymap_wwm.py       # Where Winds Meet mapping
│   ├── key_layout.py       # KeyLayout enum
│   ├── game_mode.py        # GameMode enum
│   ├── gui.py              # Tkinter song picker with validation
│   ├── config.py           # Settings persistence
│   └── logger.py           # Error logging
├── tests/                  # Test suite (362 tests)
├── assets/                 # Icons and images
├── songs/                  # MIDI files directory
├── pyproject.toml          # Project config with pinned dependencies
├── Maestro.spec            # PyInstaller build configuration
└── .github/workflows/      # CI with ruff, mypy, pip-audit
```

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Report bugs** - [Open an issue](https://github.com/nayfusaurus/maestro-keypress/issues/new)
2. **Suggest features** - Share your ideas in issues
3. **Submit PRs** - Fork, create a branch, and submit a pull request
4. **Add game support** - Create new keymap modules for other games
5. **Improve docs** - Fix typos, clarify instructions, add examples

### Development Setup

```bash
git clone https://github.com/nayfusaurus/maestro-keypress.git
cd maestro-keypress
uv sync
uv run pytest -v  # Run tests
```

Please ensure all tests pass and code is type-checked before submitting PRs.

---

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 💖 Support

If you find Maestro useful, consider:

- ⭐ **Star this repo** on GitHub
- 💰 **[Support on Ko-fi](https://ko-fi.com/nayfusaurus)** - Buy me a coffee!
- 🐛 **Report bugs** to help improve the project
- 📢 **Share** with friends who play these games

---

## 🙏 Acknowledgments

- Built with [Claude](https://claude.ai) (Anthropic)
- [mido](https://github.com/mido/mido) - MIDI file parsing
- [pynput](https://github.com/moses-palmer/pynput) - Keyboard simulation
- [pydirectinput](https://github.com/learncodebygaming/pydirectinput) - DirectInput support
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- Games: **Heartopia** and **Where Winds Meet** for inspiring this project

---

<div align="center">
  <p>Made with ❤️ for game music lovers</p>
  <p>
    <a href="#top">⬆️ Back to Top</a>
  </p>
</div>
