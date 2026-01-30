"""Main entry point for Maestro.

Coordinates hotkey listening, GUI, and playback.
"""

import threading
import time
from pathlib import Path

from pynput import keyboard

from maestro.player import Player, PlaybackState
from maestro.gui import SongPicker
from maestro.game_mode import GameMode
from maestro.config import load_config, save_config
from maestro.logger import setup_logger


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

        # Apply saved settings
        game_mode_str = self._config.get("game_mode", "Heartopia")
        for mode in GameMode:
            if mode.value == game_mode_str:
                self.player.game_mode = mode
                break
        self.player.speed = self._config.get("speed", 1.0)
        self.player.transpose = self._config.get("transpose", False)

        self.picker = SongPicker(
            songs_folder=self.songs_folder,
            on_play=self._on_play,
            on_stop=self.stop,
            get_state=self._get_state_string,
            get_position=lambda: self.player.position,
            get_duration=lambda: self.player.duration,
            get_current_song=self._get_current_song_name,
            on_exit=self._exit,
            on_game_change=self._on_game_change,
            get_last_key=lambda: self.player.last_key,
            on_speed_change=self._on_speed_change,
            get_upcoming_notes=self.player.get_upcoming_notes,
            on_lookahead_change=self._on_lookahead_change,
            initial_lookahead=self._config.get("preview_lookahead", 5),
            initial_transpose=self._config.get("transpose", False),
            initial_show_preview=self._config.get("show_preview", False),
            on_transpose_change=self._on_transpose_change,
            on_show_preview_change=self._on_show_preview_change,
        )

        self._gui_thread: threading.Thread | None = None

    def _save_config(self) -> None:
        """Save current settings to config."""
        self._config["last_songs_folder"] = str(self.songs_folder)
        self._config["game_mode"] = self.player.game_mode.value
        self._config["speed"] = self.player.speed
        save_config(self._config)

    def _on_game_change(self, mode: GameMode) -> None:
        """Handle game mode change from GUI."""
        self.player.game_mode = mode
        self._save_config()
        print(f"Game mode: {mode.value}")

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

    def _on_play(self, song_path: Path) -> None:
        """Handle play request from GUI."""
        self.player.stop()
        try:
            self.player.load(song_path)
        except Exception as e:
            error_msg = f"Cannot play {song_path.name}: {e}"
            self.logger.error(f"Failed to load '{song_path}': {e}")
            self.picker.set_error(error_msg)
            return

        # Start playback after countdown
        def countdown_play():
            for i in range(self.STARTUP_DELAY, 0, -1):
                self._countdown = i
                print(f"Playing '{song_path.stem}' in {i}...")
                time.sleep(1)
                if self.player.state == PlaybackState.PLAYING:
                    self._countdown = 0
                    return
            self._countdown = 0
            if self.player.state == PlaybackState.STOPPED:
                self.player.play()

        threading.Thread(target=countdown_play, daemon=True).start()

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

    def show_picker(self) -> None:
        """Show the song picker GUI."""
        if self._gui_thread is None or not self._gui_thread.is_alive():
            self._gui_thread = threading.Thread(target=self._run_gui, daemon=True)
            self._gui_thread.start()
        else:
            self.picker.show()

    def _run_gui(self) -> None:
        """Run the GUI in a separate thread."""
        self.picker.show()
        self.picker.run()

    def play(self) -> None:
        """Start playback if song is loaded."""
        if self.player.current_song and self.player.state == PlaybackState.STOPPED:
            self.player.play()

    def stop(self) -> None:
        """Stop playback."""
        self._countdown = 0
        self.player.stop()

    def _exit(self) -> None:
        """Exit the application."""
        print("\nExiting...")
        self._save_config()
        self.stop()
        if self._listener:
            self._listener.stop()

    def start(self) -> None:
        """Start the application with hotkey listening."""
        print("Maestro ready!")
        print("  F2: Play")
        print("  F3: Stop playback")
        print("  Ctrl+C: Exit")
        print()

        # Show GUI immediately
        self.show_picker()

        def on_press(key):
            if key == keyboard.Key.f2:
                self.play()
            elif key == keyboard.Key.f3:
                self.stop()

        self._listener = keyboard.Listener(on_press=on_press)
        self._listener.start()
        try:
            self._listener.join()
        except KeyboardInterrupt:
            self._exit()


def main():
    """Entry point."""
    app = Maestro()
    app.start()


if __name__ == "__main__":
    main()
