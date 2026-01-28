"""Main entry point for Maestro.

Coordinates hotkey listening, GUI, and playback.
"""

import sys
import threading
import time
from pathlib import Path

from pynput import keyboard

from maestro.player import Player, PlaybackState
from maestro.gui import SongPicker
from maestro.game_mode import GameMode


class Maestro:
    """Main application coordinator."""

    SONGS_FOLDER = Path("songs")
    STARTUP_DELAY = 3.0  # Seconds before playback starts

    def __init__(self, songs_folder: Path | None = None):
        """Initialize Maestro.

        Args:
            songs_folder: Path to folder containing MIDI files.
                         Defaults to ./songs
        """
        self.songs_folder = songs_folder or self.SONGS_FOLDER
        self.songs_folder.mkdir(exist_ok=True)

        self.player = Player()
        self._listener: keyboard.Listener | None = None
        self.picker = SongPicker(
            songs_folder=self.songs_folder,
            on_play=self._on_play,
            on_pause=self.toggle_pause,
            on_stop=self.stop,
            get_state=self._get_state_string,
            get_position=lambda: self.player.position,
            get_duration=lambda: self.player.duration,
            get_current_song=self._get_current_song_name,
            on_exit=self._exit,
            on_game_change=self._on_game_change,
        )

        self._gui_thread: threading.Thread | None = None

    def _on_game_change(self, mode: GameMode) -> None:
        """Handle game mode change from GUI."""
        self.player.game_mode = mode
        print(f"Game mode: {mode.value}")

    def _on_play(self, song_path: Path) -> None:
        """Handle play request from GUI."""
        self.player.stop()
        self.player.load(song_path)

        # Start playback after delay (so user can switch to game)
        def delayed_play():
            print(f"Playing '{song_path.stem}' in {self.STARTUP_DELAY} seconds...")
            time.sleep(self.STARTUP_DELAY)
            if self.player.state == PlaybackState.STOPPED:
                self.player.play()

        threading.Thread(target=delayed_play, daemon=True).start()

    def _get_state_string(self) -> str:
        """Get current playback state as string."""
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
            # GUI already running, just show it
            self.picker.show()

    def _run_gui(self) -> None:
        """Run the GUI in a separate thread."""
        self.picker.show()
        self.picker.run()

    def toggle_pause(self) -> None:
        """Toggle play/pause."""
        self.player.toggle_pause()

    def stop(self) -> None:
        """Stop playback."""
        self.player.stop()

    def _exit(self) -> None:
        """Exit the application."""
        print("\nExiting...")
        self.stop()
        if self._listener:
            self._listener.stop()

    def start(self) -> None:
        """Start the application with hotkey listening."""
        print("Maestro ready!")
        print("  F1: Open song picker")
        print("  F2: Play/Pause")
        print("  F3: Stop playback")
        print("  Ctrl+C: Exit")
        print()

        def on_press(key):
            if key == keyboard.Key.f1:
                self.show_picker()
            elif key == keyboard.Key.f2:
                self.toggle_pause()
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
