# Maestro contributor guide

[Back to the Maestro README](README.md)

## Run from source


Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/nayfusaurus/maestro-keypress.git
cd maestro-keypress
uv sync
uv run maestro
```

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

CI runs the Python test suite on Windows and Ubuntu.

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
│   ├── main.py               # App coordinator, Qt event loop, signal wiring
│   ├── player.py             # Event-driven playback engine with caching
│   ├── parser.py             # MIDI parsing with multi-tempo support
│   ├── keymap.py             # Heartopia 22-key mapping (C3-C6)
│   ├── keymap_15_double.py   # Heartopia 15-key double row
│   ├── keymap_15_triple.py   # Heartopia 15-key triple row
│   ├── keymap_drums.py       # Heartopia 8-key drums
│   ├── keymap_xylophone.py   # Heartopia 8-key xylophone
│   ├── keymap_wwm.py         # Where Winds Meet mapping (36-key Shift/Ctrl, 21-key naturals)
│   ├── keymap_once_human.py  # Once Human mapping (Shift/Ctrl octave switching)
│   ├── key_layout.py         # KeyLayout, WwmLayout enums
│   ├── game_mode.py          # GameMode enum (3 games)
│   ├── config.py             # JSON settings persistence with validation
│   ├── logger.py             # Rotating file logger
│   ├── gui/                  # PySide6 GUI package
│   │   ├── main_window.py    # MainWindow — icon rail + paged layout
│   │   ├── signals.py        # MaestroSignals (centralized Signal defs)
│   │   ├── pages/            # Dashboard, Settings, Info, Log, Stats pages
│   │   ├── song_list.py      # Rich two-line items with custom delegate
│   │   ├── piano_roll.py     # Note preview canvas
│   │   ├── controls_panel.py # Play/Stop/Favorite transport controls
│   │   ├── workers.py        # QThread workers (validation, update)
│   │   ├── theme.py          # Catppuccin dark/light themes, design tokens
│   │   └── constants.py      # Version, bindable keys, disclaimer text
├── tests/                    # Test suite
├── assets/                   # Icons and images
├── pyproject.toml            # Project config with pinned dependencies
├── Maestro.spec              # PyInstaller build configuration
└── .github/workflows/        # CI with ruff, mypy, pip-audit
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

## 🙏 Acknowledgments

- Built with [Claude](https://claude.ai) (Anthropic)
- [PySide6](https://doc.qt.io/qtforpython-6/) - Qt6 GUI framework
- [mido](https://github.com/mido/mido) - MIDI file parsing
- [pynput](https://github.com/moses-palmer/pynput) - Keyboard simulation
- [pydirectinput](https://github.com/learncodebygaming/pydirectinput) - DirectInput support
- [uv](https://github.com/astral-sh/uv) - Fast Python package manager
- Games: **Heartopia**, **Where Winds Meet**, and **Once Human** for inspiring this project
