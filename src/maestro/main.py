"""Main entry point for Maestro.

Coordinates hotkey listening, GUI, and playback.
"""

import signal
import threading
import time
from pathlib import Path

from pynput import keyboard

from maestro.player import Player, PlaybackState
from maestro.gui import SongPicker
from maestro.game_mode import GameMode
from maestro.key_layout import KeyLayout
from maestro.config import load_config, save_config
from maestro.logger import setup_logger
from maestro.parser import parse_midi

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
            on_folder_change=self._on_folder_change,
            on_layout_change=self._on_layout_change,
            initial_layout=self.player.key_layout,
            get_note_compatibility=self._get_note_compatibility,
            on_favorite_toggle=self._on_favorite_toggle,
            get_favorites=self._get_favorites,
            on_sharp_handling_change=self._on_sharp_handling_change,
            initial_sharp_handling=self._config.get("sharp_handling", "skip"),
            on_hotkey_change=self._on_hotkey_change,
            initial_play_key=self._config.get("play_key", "f2"),
            initial_stop_key=self._config.get("stop_key", "f3"),
            initial_emergency_key=self._config.get("emergency_stop_key", "escape"),
        )

        self._gui_thread: threading.Thread | None = None

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

    def _on_folder_change(self, folder: Path) -> None:
        """Handle folder change from GUI."""
        self.songs_folder = folder
        self._save_config()

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

    def _on_layout_change(self, layout: KeyLayout) -> None:
        """Handle key layout change from GUI."""
        self.player.key_layout = layout
        self._config["key_layout"] = layout.value
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
        return self._config.get("favorites", [])

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

    def _on_play(self, song_path: Path) -> None:
        """Handle play request from GUI."""
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
        play_key = self._get_hotkey("play_key", "f2")
        stop_key = self._get_hotkey("stop_key", "f3")
        emergency_key = self._get_hotkey("emergency_stop_key", "escape")

        # Show help text with configured keys
        play_name = self._config.get("play_key", "f2").upper()
        stop_name = self._config.get("stop_key", "f3").upper()
        emergency_name = self._config.get("emergency_stop_key", "escape").upper()

        print("Maestro ready!")
        print(f"  {play_name}: Play")
        print(f"  {stop_name}: Stop playback")
        print(f"  {emergency_name}: Emergency stop")
        print("  Ctrl+C: Exit")
        print()

        # Show GUI immediately
        self.show_picker()

        def _handle_signal(signum, frame):
            self.player._release_all_keys()
            self._exit()

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        def on_press(key):
            if key == play_key:
                self.play()
            elif key == stop_key:
                self.stop()
            # Escape is ALWAYS an emergency stop, regardless of config
            if key == keyboard.Key.esc:
                self.player._release_all_keys()
                self.stop()
            elif key == emergency_key and emergency_key != keyboard.Key.esc:
                self.player._release_all_keys()
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
