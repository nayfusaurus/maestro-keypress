"""Tkinter GUI for song selection.

Provides a simple window to browse and select MIDI files.
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Callable


def get_songs_from_folder(folder: Path) -> list[Path]:
    """Get all MIDI files from a folder.

    Args:
        folder: Path to the songs folder

    Returns:
        List of paths to .mid files, sorted alphabetically
    """
    if not folder.exists():
        return []

    return sorted(folder.glob("*.mid"))


class SongPicker:
    """GUI window for selecting songs."""

    def __init__(
        self,
        songs_folder: Path,
        on_play: Callable[[Path], None],
        on_pause: Callable[[], None],
        on_stop: Callable[[], None],
        get_state: Callable[[], str],
    ):
        """Initialize the song picker.

        Args:
            songs_folder: Path to folder containing MIDI files
            on_play: Callback when play is clicked with selected song path
            on_pause: Callback when pause is clicked
            on_stop: Callback when stop is clicked
            get_state: Callback to get current playback state string
        """
        self.songs_folder = songs_folder
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_stop = on_stop
        self.get_state = get_state

        self.window: tk.Tk | None = None
        self.song_listbox: tk.Listbox | None = None
        self.status_label: tk.Label | None = None
        self._songs: list[Path] = []

    def show(self) -> None:
        """Show the song picker window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            self._refresh_songs()
            return

        self.window = tk.Tk()
        self.window.title("Maestro - Song Picker")
        self.window.geometry("350x450")
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Song list
        list_frame = ttk.Frame(self.window)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(list_frame, text="Songs:").pack(anchor=tk.W)

        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.song_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set)
        self.song_listbox.pack(fill=tk.BOTH, expand=True)
        self.song_listbox.bind("<Double-1>", self._on_double_click)
        scrollbar.config(command=self.song_listbox.yview)

        # Control buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Play", command=self._on_play_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Pause", command=self._on_pause_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Stop", command=self._on_stop_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_songs).pack(side=tk.RIGHT, padx=2)

        # Status
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Status: Stopped")
        self.status_label.pack(anchor=tk.W)

        self._refresh_songs()
        self._update_status()

    def _refresh_songs(self) -> None:
        """Refresh the song list from disk."""
        if self.song_listbox is None:
            return

        self._songs = get_songs_from_folder(self.songs_folder)
        self.song_listbox.delete(0, tk.END)

        for song in self._songs:
            self.song_listbox.insert(tk.END, song.stem)

    def _get_selected_song(self) -> Path | None:
        """Get the currently selected song path."""
        if self.song_listbox is None:
            return None

        selection = self.song_listbox.curselection()
        if not selection:
            return None
        return self._songs[selection[0]]

    def _on_play_click(self) -> None:
        """Handle play button click."""
        song = self._get_selected_song()
        if song:
            self.on_play(song)
            self._update_status()

    def _on_pause_click(self) -> None:
        """Handle pause button click."""
        self.on_pause()
        self._update_status()

    def _on_stop_click(self) -> None:
        """Handle stop button click."""
        self.on_stop()
        self._update_status()

    def _on_double_click(self, event) -> None:
        """Handle double-click on song."""
        self._on_play_click()

    def _update_status(self) -> None:
        """Update the status label."""
        if self.status_label:
            state = self.get_state()
            self.status_label.config(text=f"Status: {state}")

    def _on_close(self) -> None:
        """Handle window close."""
        if self.window:
            self.window.destroy()
            self.window = None
            self.song_listbox = None
            self.status_label = None

    def run(self) -> None:
        """Run the Tkinter main loop (blocking)."""
        if self.window:
            self.window.mainloop()

    def close(self) -> None:
        """Close the window."""
        self._on_close()
