"""Tkinter GUI for song selection.

Provides a simple window to browse and select MIDI files.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Callable

from maestro.game_mode import GameMode


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
        get_position: Callable[[], float] | None = None,
        get_duration: Callable[[], float] | None = None,
        get_current_song: Callable[[], str | None] | None = None,
        on_exit: Callable[[], None] | None = None,
        on_game_change: Callable[[GameMode], None] | None = None,
    ):
        """Initialize the song picker.

        Args:
            songs_folder: Path to folder containing MIDI files
            on_play: Callback when play is clicked with selected song path
            on_pause: Callback when pause is clicked
            on_stop: Callback when stop is clicked
            get_state: Callback to get current playback state string
            get_position: Callback to get current playback position in seconds
            get_duration: Callback to get total song duration in seconds
            get_current_song: Callback to get current song name
            on_exit: Callback when window is closed to exit app
            on_game_change: Callback when game mode is changed
        """
        self.songs_folder = songs_folder
        self.on_play = on_play
        self.on_pause = on_pause
        self.on_stop = on_stop
        self.get_state = get_state
        self.get_position = get_position
        self.get_duration = get_duration
        self.get_current_song = get_current_song
        self.on_exit = on_exit
        self.on_game_change = on_game_change

        self.window: tk.Tk | None = None
        self.song_listbox: tk.Listbox | None = None
        self.status_label: tk.Label | None = None
        self.folder_label: tk.Label | None = None
        self.search_var: tk.StringVar | None = None
        self.progress_bar: ttk.Progressbar | None = None
        self.progress_label: tk.Label | None = None
        self.song_info_label: tk.Label | None = None
        self.game_mode_var: tk.StringVar | None = None
        self._songs: list[Path] = []
        self._filtered_songs: list[Path] = []
        self._update_job: str | None = None

    def show(self) -> None:
        """Show the song picker window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            self._refresh_songs()
            return

        self.window = tk.Tk()
        self.window.title("Maestro - Song Picker")
        self.window.geometry("400x550")
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Folder selection
        folder_frame = ttk.Frame(self.window)
        folder_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Browse...", command=self._on_browse_click).pack(side=tk.RIGHT)
        self.folder_label = ttk.Label(folder_frame, text=str(self.songs_folder), foreground="gray")
        self.folder_label.pack(side=tk.LEFT, padx=(5, 0), fill=tk.X, expand=True)

        # Game mode selection
        game_frame = ttk.Frame(self.window)
        game_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Label(game_frame, text="Game:").pack(side=tk.LEFT)
        self.game_mode_var = tk.StringVar(value=GameMode.HEARTOPIA.value)
        game_dropdown = ttk.Combobox(
            game_frame,
            textvariable=self.game_mode_var,
            values=[mode.value for mode in GameMode],
            state="readonly",
            width=20,
        )
        game_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        game_dropdown.bind("<<ComboboxSelected>>", self._on_game_mode_change)

        # Search bar
        search_frame = ttk.Frame(self.window)
        search_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

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

        # Now Playing info
        info_frame = ttk.LabelFrame(self.window, text="Now Playing")
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.song_info_label = ttk.Label(info_frame, text="No song loaded")
        self.song_info_label.pack(anchor=tk.W, padx=5, pady=(5, 0))

        # Progress bar
        progress_frame = ttk.Frame(info_frame)
        progress_frame.pack(fill=tk.X, padx=5, pady=5)

        self.progress_bar = ttk.Progressbar(progress_frame, mode="determinate", length=200)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress_label = ttk.Label(progress_frame, text="0:00 / 0:00")
        self.progress_label.pack(side=tk.RIGHT, padx=(10, 0))

        # Status
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Status: Stopped")
        self.status_label.pack(anchor=tk.W)

        self._refresh_songs()
        self._update_status()
        self._start_progress_updates()

    def _refresh_songs(self) -> None:
        """Refresh the song list from disk."""
        if self.song_listbox is None:
            return

        self._songs = get_songs_from_folder(self.songs_folder)
        self._apply_search_filter()

    def _apply_search_filter(self) -> None:
        """Apply current search filter to song list."""
        if self.song_listbox is None:
            return

        search_term = self.search_var.get().lower() if self.search_var else ""

        if search_term:
            self._filtered_songs = [s for s in self._songs if search_term in s.stem.lower()]
        else:
            self._filtered_songs = self._songs.copy()

        self.song_listbox.delete(0, tk.END)
        for song in self._filtered_songs:
            self.song_listbox.insert(tk.END, song.stem)

    def _on_search_change(self, *args) -> None:
        """Handle search text change."""
        self._apply_search_filter()

    def _get_selected_song(self) -> Path | None:
        """Get the currently selected song path."""
        if self.song_listbox is None:
            return None

        selection = self.song_listbox.curselection()
        if not selection:
            return None
        return self._filtered_songs[selection[0]]

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

    def _on_browse_click(self) -> None:
        """Handle browse button click."""
        folder = filedialog.askdirectory(
            title="Select Songs Folder",
            initialdir=str(self.songs_folder),
        )
        if folder:
            self.songs_folder = Path(folder)
            if self.folder_label:
                self.folder_label.config(text=str(self.songs_folder))
            self._refresh_songs()

    def _on_game_mode_change(self, event=None) -> None:
        """Handle game mode dropdown change."""
        if self.on_game_change and self.game_mode_var:
            selected = self.game_mode_var.get()
            for mode in GameMode:
                if mode.value == selected:
                    self.on_game_change(mode)
                    break

    def _update_status(self) -> None:
        """Update the status label."""
        if self.status_label:
            state = self.get_state()
            self.status_label.config(text=f"Status: {state}")

    def _format_time(self, seconds: float) -> str:
        """Format seconds as M:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def _start_progress_updates(self) -> None:
        """Start periodic progress bar updates."""
        self._update_progress()

    def _update_progress(self) -> None:
        """Update progress bar and info labels."""
        if self.window is None:
            return

        # Update song info
        if self.song_info_label and self.get_current_song:
            song_name = self.get_current_song()
            if song_name:
                self.song_info_label.config(text=song_name)
            else:
                self.song_info_label.config(text="No song loaded")

        # Update progress bar
        position = self.get_position() if self.get_position else 0.0
        duration = self.get_duration() if self.get_duration else 0.0

        if self.progress_bar:
            if duration > 0:
                progress = (position / duration) * 100
                self.progress_bar["value"] = progress
            else:
                self.progress_bar["value"] = 0

        if self.progress_label:
            self.progress_label.config(
                text=f"{self._format_time(position)} / {self._format_time(duration)}"
            )

        # Update status
        self._update_status()

        # Schedule next update
        self._update_job = self.window.after(200, self._update_progress)

    def _on_close(self) -> None:
        """Handle window close."""
        if self._update_job and self.window:
            self.window.after_cancel(self._update_job)
            self._update_job = None

        if self.window:
            self.window.destroy()
            self.window = None
            self.song_listbox = None
            self.status_label = None
            self.folder_label = None
            self.search_var = None
            self.progress_bar = None
            self.progress_label = None
            self.song_info_label = None
            self.game_mode_var = None

        # Exit the entire app
        if self.on_exit:
            self.on_exit()

    def run(self) -> None:
        """Run the Tkinter main loop (blocking)."""
        if self.window:
            self.window.mainloop()

    def close(self) -> None:
        """Close the window."""
        self._on_close()
