"""Main entry point for Maestro.

Coordinates hotkey listening, GUI, and playback.
"""

import signal
import sys
from pathlib import Path

from pynput import keyboard

from maestro.config import load_config, save_config
from maestro.game_mode import GameMode
from maestro.key_layout import KeyLayout
from maestro.logger import setup_logger
from maestro.parser import parse_midi
from maestro.player import PlaybackState, Player

KEY_NAME_MAP = {
    "f1": keyboard.Key.f1,
    "f2": keyboard.Key.f2,
    "f3": keyboard.Key.f3,
    "f4": keyboard.Key.f4,
    "f5": keyboard.Key.f5,
    "f6": keyboard.Key.f6,
    "f7": keyboard.Key.f7,
    "f8": keyboard.Key.f8,
    "f9": keyboard.Key.f9,
    "f10": keyboard.Key.f10,
    "f11": keyboard.Key.f11,
    "f12": keyboard.Key.f12,
    "escape": keyboard.Key.esc,
    "home": keyboard.Key.home,
    "end": keyboard.Key.end,
    "insert": keyboard.Key.insert,
    "delete": keyboard.Key.delete,
    "page_up": keyboard.Key.page_up,
    "page_down": keyboard.Key.page_down,
}


class Maestro:
    """Main application coordinator."""

    SONGS_FOLDER = Path("songs")
    STARTUP_DELAY = 3  # Seconds before playback starts

    def __init__(self, songs_folder: Path | None = None):
        """Initialize Maestro."""
        self.logger = setup_logger()
        self._config = load_config()

        # Use provided folder, or config folder, or default
        if songs_folder:
            self.songs_folder = songs_folder
        elif self._config.get("last_songs_folder"):
            self.songs_folder = Path(self._config["last_songs_folder"])
        else:
            self.songs_folder = self.SONGS_FOLDER

        self.songs_folder.mkdir(exist_ok=True)

        self.player = Player()
        self._listener: keyboard.Listener | None = None
        self._countdown: int = 0
        self._countdown_timer = None
        self._update_timer = None
        self._prev_push_state: str = "Stopped"
        self._import_worker = None

        # Apply saved settings
        game_mode_str = self._config.get("game_mode", "Heartopia")
        for mode in GameMode:
            if mode.value == game_mode_str:
                self.player.game_mode = mode
                break
        self.player.speed = self._config.get("speed", 1.0)
        self.player.transpose = self._config.get("transpose", False)

        # Restore key layout
        layout_str = self._config.get("key_layout", "22-key (Full)")
        for layout in KeyLayout:
            if layout.value == layout_str:
                self.player.key_layout = layout
                break

        # Restore sharp handling
        self.player.sharp_handling = self._config.get("sharp_handling", "skip")

        self.window = None  # Created in start()

    def _get_hotkey(self, config_key: str, default: str) -> keyboard.Key | None:
        """Get a pynput Key from config string name."""
        key_name = self._config.get(config_key, default)
        return KEY_NAME_MAP.get(key_name)

    def _save_config(self) -> None:
        """Save current settings to config."""
        self._config["last_songs_folder"] = str(self.songs_folder)
        self._config["game_mode"] = self.player.game_mode.value
        self._config["speed"] = self.player.speed
        save_config(self._config)

    def _connect_signals(self) -> None:
        """Wire GUI signals to Maestro slots."""
        s = self.window.signals

        # User action signals
        s.play_requested.connect(self._on_play)
        s.stop_requested.connect(self.stop)
        s.exit_requested.connect(self._exit)
        s.game_mode_changed.connect(self._on_game_change)
        s.folder_changed.connect(self._on_folder_change)
        s.layout_changed.connect(self._on_layout_change)
        s.speed_changed.connect(self._on_speed_change)
        s.lookahead_changed.connect(self._on_lookahead_change)
        s.transpose_changed.connect(self._on_transpose_change)
        s.show_preview_changed.connect(self._on_show_preview_change)
        s.favorite_toggled.connect(self._on_favorite_toggle)
        s.sharp_handling_changed.connect(self._on_sharp_handling_change)
        s.hotkey_changed.connect(self._on_hotkey_change)
        s.theme_changed.connect(self._on_theme_change)
        s.note_compatibility_requested.connect(self._on_note_compatibility_requested)
        s.import_requested.connect(self._on_import_requested)

        # Disclaimer acceptance from info page
        self.window._info.disclaimer_accepted.connect(self._on_disclaimer_accepted)

    def _push_state_updates(self) -> None:
        """Push current state to GUI via signals. Called every 200ms by QTimer."""
        if self.window is None:
            return

        s = self.window.signals

        # State
        state_str = self._get_state_string()
        s.state_updated.emit(state_str)

        # Position
        s.position_updated.emit(self.player.position, self.player.duration)

        # Current song
        name = self._get_current_song_name() or ""
        s.current_song_updated.emit(name)

        # Last key
        s.last_key_updated.emit(self.player.last_key)

        # Upcoming notes (for piano roll)
        lookahead = self._config.get("preview_lookahead", 5)
        notes = self.player.get_upcoming_notes(float(lookahead))
        s.upcoming_notes_updated.emit(notes)

        # Detect song finish (PLAYING -> STOPPED transition)
        if self._prev_push_state == "Playing" and state_str == "Stopped":
            s.song_finished.emit()
        self._prev_push_state = state_str

    def _on_folder_change(self, folder) -> None:
        """Handle folder change from GUI."""
        self.songs_folder = Path(folder) if not isinstance(folder, Path) else folder
        self._save_config()

    def _on_game_change(self, mode_str: str) -> None:
        """Handle game mode change from GUI."""
        for mode in GameMode:
            if mode.value == mode_str:
                self.player.game_mode = mode
                break
        self._save_config()
        print(f"Game mode: {mode_str}")

    def _on_speed_change(self, speed: float) -> None:
        """Handle speed change from GUI."""
        self.player.speed = speed
        self._save_config()

    def _on_lookahead_change(self, lookahead: int) -> None:
        """Handle lookahead change from GUI."""
        self._config["preview_lookahead"] = lookahead
        self._save_config()

    def _on_transpose_change(self, transpose: bool) -> None:
        """Handle transpose setting change from GUI."""
        self.player.transpose = transpose
        self._config["transpose"] = transpose
        self._save_config()

    def _on_show_preview_change(self, show_preview: bool) -> None:
        """Handle show preview setting change from GUI."""
        self._config["show_preview"] = show_preview
        self._save_config()

    def _on_layout_change(self, layout_str: str) -> None:
        """Handle key layout change from GUI."""
        for layout in KeyLayout:
            if layout.value == layout_str:
                self.player.key_layout = layout
                self._config["key_layout"] = layout.value
                break
        self._save_config()

    def _on_favorite_toggle(self, song_name: str, is_favorite: bool) -> None:
        """Handle favorite toggle from GUI."""
        favorites = self._config.get("favorites", [])
        if is_favorite and song_name not in favorites:
            favorites.append(song_name)
        elif not is_favorite and song_name in favorites:
            favorites.remove(song_name)
        self._config["favorites"] = favorites
        self._save_config()

    def _get_favorites(self) -> list[str]:
        """Get list of favorite song names."""
        favorites: list[str] = self._config.get("favorites", [])
        return favorites

    def _on_sharp_handling_change(self, handling: str) -> None:
        """Handle sharp handling change from GUI."""
        self.player.sharp_handling = handling
        self._config["sharp_handling"] = handling
        self._save_config()

    def _on_hotkey_change(self, config_key: str, key_name: str) -> None:
        """Handle hotkey change from GUI."""
        self._config[config_key] = key_name
        self._save_config()
        print(f"Hotkey '{config_key}' changed to '{key_name}'")

    def _on_theme_change(self, theme: str) -> None:
        """Handle theme change from GUI."""
        self._config["theme"] = theme
        self._save_config()

    def _on_disclaimer_accepted(self) -> None:
        """Handle disclaimer acceptance from info page."""
        self._config["disclaimer_accepted"] = True
        self._save_config()
        # Send favorites to GUI now that disclaimer is accepted
        if self.window:
            self.window.signals.favorites_loaded.emit(self._get_favorites())

    def _on_note_compatibility_requested(self, song_path) -> None:
        """Calculate note compatibility and emit result back to GUI."""
        song_path = Path(song_path) if not isinstance(song_path, Path) else song_path
        playable, total = self._get_note_compatibility(song_path)
        if self.window:
            self.window.signals.note_compatibility_result.emit(playable, total)

    def _get_note_compatibility(self, song_path: Path) -> tuple[int, int]:
        """Calculate how many notes in a song are playable with current layout.

        Returns:
            Tuple of (playable_count, total_count)
        """
        try:
            notes = parse_midi(song_path)
        except Exception:
            return (0, 0)

        playable = 0
        total = len(notes)
        for note in notes:
            result = self.player._resolve_key(note.midi_note)
            if result is not None:
                playable += 1

        return (playable, total)

    def _on_import_requested(self, url: str, isolate_piano: bool = False) -> None:
        """Handle import request from GUI."""
        from maestro.gui.workers import ImportWorker

        self._import_worker = ImportWorker(
            url=url,
            dest_folder=self.songs_folder,
            isolate_piano=isolate_piano,
        )
        self._import_worker.progress.connect(
            lambda text: self.window.signals.import_progress.emit(text)
        )
        self._import_worker.finished.connect(
            lambda filename: self.window.signals.import_finished.emit(filename)
        )
        self._import_worker.error.connect(
            lambda msg: self.window.signals.import_error.emit(msg)
        )
        self._import_worker.start()

    def _on_play(self, song_path) -> None:
        """Handle play request from GUI."""
        from PySide6.QtCore import QTimer

        song_path = Path(song_path) if not isinstance(song_path, Path) else song_path
        self.player.stop()

        # Track recently played
        recently = self._config.get("recently_played", [])
        song_name = song_path.stem
        if song_name in recently:
            recently.remove(song_name)
        recently.insert(0, song_name)
        self._config["recently_played"] = recently[:20]  # Cap at 20
        self._save_config()

        try:
            self.player.load(song_path)
        except Exception as e:
            error_msg = f"Cannot play {song_path.name}: {e}"
            self.logger.error(f"Failed to load '{song_path}': {e}")
            if self.window:
                self.window.signals.error_occurred.emit(error_msg)
            return

        # Start countdown using QTimer instead of sleep-based thread
        self._countdown = self.STARTUP_DELAY
        if self.window:
            self.window.signals.countdown_tick.emit(self._countdown)

        self._countdown_timer = QTimer()
        self._countdown_timer.timeout.connect(self._countdown_step)
        self._countdown_timer.start(1000)

    def _countdown_step(self) -> None:
        """Handle one tick of the countdown timer."""
        self._countdown -= 1

        if self.window:
            self.window.signals.countdown_tick.emit(self._countdown)

        if self._countdown <= 0:
            if self._countdown_timer:
                self._countdown_timer.stop()
                self._countdown_timer = None
            if self.player.state == PlaybackState.STOPPED:
                self.player.play()

    def _get_state_string(self) -> str:
        """Get current playback state as string."""
        if self._countdown > 0:
            return f"Starting in {self._countdown}..."
        return self.player.state.name.capitalize()

    def _get_current_song_name(self) -> str | None:
        """Get current song name."""
        if self.player.current_song:
            return self.player.current_song.stem
        return None

    def play(self) -> None:
        """Start playback if song is loaded."""
        if self.player.current_song and self.player.state == PlaybackState.STOPPED:
            self.player.play()

    def stop(self) -> None:
        """Stop playback."""
        self._countdown = 0
        if self._countdown_timer:
            self._countdown_timer.stop()
            self._countdown_timer = None
        self.player.stop()

    def _exit(self) -> None:
        """Exit the application."""
        from PySide6.QtWidgets import QApplication

        print("\nExiting...")
        self._save_config()
        self.stop()
        if self._listener:
            self._listener.stop()
        QApplication.quit()

    def start(self) -> None:
        """Start the application with Qt event loop on main thread."""
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        # Set AppUserModelID so Windows taskbar shows our icon instead of
        # the default Python/PyInstaller icon.
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("maestro.app")  # type: ignore[union-attr]

        app = QApplication(sys.argv)

        # Set app icon immediately — BEFORE any window is shown.
        # Windows assigns the taskbar icon when the first window appears,
        # so this must happen before the splash screen.
        from PySide6.QtGui import QIcon
        if getattr(sys, "frozen", False):
            _base = Path(getattr(sys, "_MEIPASS", ""))
        else:
            _base = Path(__file__).resolve().parent.parent.parent
        # Prefer .ico (multi-size, better for Windows taskbar), fall back to .png
        _icon_path = _base / "assets" / "icon.ico"
        if not _icon_path.exists():
            _icon_path = _base / "assets" / "icon.png"
        if _icon_path.exists():
            app.setWindowIcon(QIcon(str(_icon_path)))

        # Show splash screen immediately (before heavy imports)
        from maestro.gui.splash import SplashScreen

        splash = SplashScreen()
        splash.show()
        app.processEvents()

        # Stage 1: Load theme
        splash.set_progress(20, "Loading theme...")
        app.processEvents()
        from maestro.gui.theme import apply_theme

        apply_theme(app)

        # Stage 2: Load GUI modules
        splash.set_progress(50, "Loading interface...")
        app.processEvents()
        from maestro.gui import MainWindow

        # Stage 3: Build main window (scans songs folder)
        splash.set_progress(80, "Preparing songs...")
        app.processEvents()
        self.window = MainWindow(
            songs_folder=self.songs_folder,
            config=self._config,
        )
        self._connect_signals()

        # Send initial favorites to GUI (skip if first launch — disclaimer not yet accepted)
        if self._config.get("disclaimer_accepted", False):
            self.window.signals.favorites_loaded.emit(self._get_favorites())

        # Stage 4: Show window and close splash
        splash.set_progress(100, "Ready")
        app.processEvents()
        self.window.show()
        splash.close()
        splash.deleteLater()

        # Start pynput listener (non-blocking, runs in its own thread)
        self._setup_listener()

        # Start 200ms update timer for state pushes
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._push_state_updates)
        self._update_timer.start(200)

        # Signal handlers — need a timer for signal delivery in Qt
        def _handle_signal(signum, frame):
            self.player._release_all_keys()
            self._exit()

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        # Timer to allow Python signal handlers to fire within Qt event loop
        self._signal_timer = QTimer()
        self._signal_timer.timeout.connect(lambda: None)
        self._signal_timer.start(500)

        # Show help text
        play_name = self._config.get("play_key", "f2").upper()
        stop_name = self._config.get("stop_key", "f3").upper()
        emergency_name = self._config.get("emergency_stop_key", "escape").upper()

        print("Maestro ready!")
        print(f"  {play_name}: Play")
        print(f"  {stop_name}: Stop playback")
        print(f"  {emergency_name}: Emergency stop")
        print("  Ctrl+C: Exit")
        print()

        sys.exit(app.exec())

    def _setup_listener(self) -> None:
        """Set up and start the pynput keyboard listener."""
        play_key = self._get_hotkey("play_key", "f2")
        stop_key = self._get_hotkey("stop_key", "f3")
        emergency_key = self._get_hotkey("emergency_stop_key", "escape")

        def on_press(key):
            if key == play_key:
                self.play()
            elif key == stop_key:
                self.stop()
            # Escape is ALWAYS an emergency stop, regardless of config
            if (
                key == keyboard.Key.esc
                or key == emergency_key
                and emergency_key != keyboard.Key.esc
            ):
                self.player._release_all_keys()
                self.stop()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()


def main():
    """Entry point."""
    app = Maestro()
    app.start()


if __name__ == "__main__":
    main()
