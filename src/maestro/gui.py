"""Tkinter GUI for song selection.

Provides a simple window to browse and select MIDI files.
"""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Callable
import webbrowser

from maestro.game_mode import GameMode
from maestro.logger import open_log_file

# App info
APP_VERSION = "1.0.0"
KOFI_URL = "https://ko-fi.com/nayfusaurus"


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
        on_stop: Callable[[], None],
        get_state: Callable[[], str],
        get_position: Callable[[], float] | None = None,
        get_duration: Callable[[], float] | None = None,
        get_current_song: Callable[[], str | None] | None = None,
        on_exit: Callable[[], None] | None = None,
        on_game_change: Callable[[GameMode], None] | None = None,
        get_last_key: Callable[[], str] | None = None,
        on_speed_change: Callable[[float], None] | None = None,
        get_upcoming_notes: Callable[[float], list] | None = None,
        on_lookahead_change: Callable[[int], None] | None = None,
        initial_lookahead: int = 5,
        initial_transpose: bool = False,
        initial_show_preview: bool = False,
        on_transpose_change: Callable[[bool], None] | None = None,
        on_show_preview_change: Callable[[bool], None] | None = None,
    ):
        """Initialize the song picker.

        Args:
            songs_folder: Path to folder containing MIDI files
            on_play: Callback when play is clicked with selected song path
            on_stop: Callback when stop is clicked
            get_state: Callback to get current playback state string
            get_position: Callback to get current playback position in seconds
            get_duration: Callback to get total song duration in seconds
            get_current_song: Callback to get current song name
            on_exit: Callback when window is closed to exit app
            on_game_change: Callback when game mode is changed
            get_last_key: Callback to get last key pressed
            on_speed_change: Callback when playback speed is changed
            get_upcoming_notes: Callback to get upcoming notes for preview
            on_lookahead_change: Callback when lookahead is changed
            initial_lookahead: Initial lookahead value in seconds
            initial_transpose: Initial transpose setting
            initial_show_preview: Initial show preview setting
            on_transpose_change: Callback when transpose setting changes
            on_show_preview_change: Callback when show preview setting changes
        """
        self.songs_folder = songs_folder
        self.on_play = on_play
        self.on_stop = on_stop
        self.get_state = get_state
        self.get_position = get_position
        self.get_duration = get_duration
        self.get_current_song = get_current_song
        self.on_exit = on_exit
        self.on_game_change = on_game_change
        self.get_last_key = get_last_key
        self.on_speed_change = on_speed_change
        self.get_upcoming_notes = get_upcoming_notes
        self.on_lookahead_change = on_lookahead_change
        self.on_transpose_change = on_transpose_change
        self.on_show_preview_change = on_show_preview_change
        self._lookahead = initial_lookahead
        self._transpose = initial_transpose
        self._show_preview = initial_show_preview

        self.window: tk.Tk | None = None
        self.song_listbox: tk.Listbox | None = None
        self.status_label: tk.Label | None = None
        self.folder_label: tk.Label | None = None
        self.search_var: tk.StringVar | None = None
        self.progress_bar: ttk.Progressbar | None = None
        self.progress_label: tk.Label | None = None
        self.song_info_label: tk.Label | None = None
        self.game_mode_var: tk.StringVar | None = None
        self.key_label: tk.Label | None = None
        self.speed_var: tk.DoubleVar | None = None
        self.speed_label: tk.Label | None = None
        self.preview_canvas: tk.Canvas | None = None
        self.lookahead_var: tk.IntVar | None = None
        self.preview_frame: ttk.LabelFrame | None = None
        self.error_label: tk.Label | None = None
        self._songs: list[Path] = []
        self._filtered_songs: list[Path] = []
        self._update_job: str | None = None
        self._last_error: str = ""

    def set_error(self, message: str) -> None:
        """Set error message to display in status."""
        self._last_error = message

    def show(self) -> None:
        """Show the song picker window."""
        if self.window is not None:
            self.window.lift()
            self.window.focus_force()
            self._refresh_songs()
            return

        self.window = tk.Tk()
        self.window.title("Maestro - Song Picker")
        self.window.geometry("400x700")
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Menu bar
        self._create_menu_bar()

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

        # Speed control
        speed_frame = ttk.Frame(self.window)
        speed_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Label(speed_frame, text="Speed:").pack(side=tk.LEFT)
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_slider = ttk.Scale(
            speed_frame,
            from_=0.25,
            to=1.5,
            variable=self.speed_var,
            orient=tk.HORIZONTAL,
            command=self._on_speed_change,
        )
        speed_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
        self.speed_label = ttk.Label(speed_frame, text="1.0x", width=5)
        self.speed_label.pack(side=tk.LEFT)

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
        ttk.Button(btn_frame, text="Stop", command=self._on_stop_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_songs).pack(side=tk.RIGHT, padx=2)

        # Error label (above Now Playing)
        self.error_label = tk.Label(
            self.window,
            text="",
            foreground="red",
            font=("TkDefaultFont", 10, "bold"),
            wraplength=380,
        )
        # Don't pack yet - only show when there's an error

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

        # Note Preview (conditionally shown)
        self.preview_frame = ttk.LabelFrame(self.window, text="Note Preview")

        # Lookahead selector
        lookahead_row = ttk.Frame(self.preview_frame)
        lookahead_row.pack(fill=tk.X, padx=5, pady=(5, 0))

        ttk.Label(lookahead_row, text="Lookahead:").pack(side=tk.LEFT)
        self.lookahead_var = tk.IntVar(value=self._lookahead)
        lookahead_dropdown = ttk.Combobox(
            lookahead_row,
            textvariable=self.lookahead_var,
            values=["2", "5", "10"],
            state="readonly",
            width=5,
        )
        lookahead_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        lookahead_dropdown.bind("<<ComboboxSelected>>", self._on_lookahead_change)
        ttk.Label(lookahead_row, text="seconds").pack(side=tk.LEFT, padx=(5, 0))

        # Canvas for piano roll
        self.preview_canvas = tk.Canvas(self.preview_frame, height=80, bg="black")
        self.preview_canvas.pack(fill=tk.X, padx=5, pady=5)

        # Show/hide preview based on setting
        if self._show_preview:
            self.preview_frame.pack(fill=tk.X, padx=10, pady=5)

        # Status and Key display
        status_frame = ttk.Frame(self.window)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        self.status_label = ttk.Label(status_frame, text="Status: Stopped")
        self.status_label.pack(side=tk.LEFT)

        self.key_label = ttk.Label(status_frame, text="Key: -", font=("TkDefaultFont", 10, "bold"))
        self.key_label.pack(side=tk.RIGHT, padx=(0, 10))

        self._refresh_songs()
        self._update_status()
        self._start_progress_updates()

    def _create_menu_bar(self) -> None:
        """Create the menu bar."""
        if self.window is None:
            return

        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Log", command=self._on_open_log_click)
        file_menu.add_command(label="Settings...", command=self._show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)

    def _show_settings(self) -> None:
        """Show the Settings dialog."""
        if self.window is None:
            return

        settings = tk.Toplevel(self.window)
        settings.title("Settings")
        settings.geometry("300x150")
        settings.resizable(False, False)
        settings.transient(self.window)
        settings.grab_set()

        # Center on parent window
        settings.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 300) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 150) // 2
        settings.geometry(f"+{x}+{y}")

        # Transpose checkbox
        transpose_var = tk.BooleanVar(value=self._transpose)
        transpose_cb = ttk.Checkbutton(
            settings,
            text="Transpose notes to playable range",
            variable=transpose_var,
            command=lambda: self._on_transpose_toggle(transpose_var.get()),
        )
        transpose_cb.pack(anchor=tk.W, padx=20, pady=(20, 10))

        # Show preview checkbox
        preview_var = tk.BooleanVar(value=self._show_preview)
        preview_cb = ttk.Checkbutton(
            settings,
            text="Show note preview panel",
            variable=preview_var,
            command=lambda: self._on_show_preview_toggle(preview_var.get()),
        )
        preview_cb.pack(anchor=tk.W, padx=20, pady=(0, 20))

        # Close button
        ttk.Button(settings, text="Close", command=settings.destroy).pack(pady=(0, 20))

    def _on_transpose_toggle(self, value: bool) -> None:
        """Handle transpose checkbox toggle."""
        self._transpose = value
        if self.on_transpose_change:
            self.on_transpose_change(value)

    def _on_show_preview_toggle(self, value: bool) -> None:
        """Handle show preview checkbox toggle."""
        self._show_preview = value
        if self.preview_frame:
            if value:
                self.preview_frame.pack(fill=tk.X, padx=10, pady=5)
            else:
                self.preview_frame.pack_forget()
        if self.on_show_preview_change:
            self.on_show_preview_change(value)

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
        self._last_error = ""
        self._update_error_label()
        song = self._get_selected_song()
        if song:
            self.on_play(song)
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

    def _on_speed_change(self, value: str) -> None:
        """Handle speed slider change."""
        speed = float(value)
        if self.speed_label:
            self.speed_label.config(text=f"{speed:.2f}x")
        if self.on_speed_change:
            self.on_speed_change(speed)

    def _on_lookahead_change(self, event=None) -> None:
        """Handle lookahead dropdown change."""
        if self.lookahead_var:
            self._lookahead = self.lookahead_var.get()
            if self.on_lookahead_change:
                self.on_lookahead_change(self._lookahead)

    def _on_open_log_click(self) -> None:
        """Handle Open Log menu item click."""
        open_log_file()

    def _show_about(self) -> None:
        """Show the About dialog."""
        if self.window is None:
            return

        about = tk.Toplevel(self.window)
        about.title("About Maestro")
        about.geometry("300x220")
        about.resizable(False, False)
        about.transient(self.window)
        about.grab_set()

        # Center on parent window
        about.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 300) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 220) // 2
        about.geometry(f"+{x}+{y}")

        # Title
        ttk.Label(
            about,
            text="Maestro",
            font=("TkDefaultFont", 16, "bold")
        ).pack(pady=(20, 5))

        # Version
        ttk.Label(about, text=f"Version {APP_VERSION}").pack()

        # Description
        ttk.Label(
            about,
            text="MIDI Piano Player for Games",
            foreground="gray"
        ).pack(pady=(5, 15))

        # Credits
        ttk.Label(about, text="Created by Yannick Wurm").pack()

        # Separator
        ttk.Separator(about, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=15)

        # Support section
        ttk.Label(about, text="Like this tool? Support development:").pack()

        # Ko-fi link button
        kofi_btn = ttk.Button(
            about,
            text="Buy me a coffee on Ko-fi",
            command=lambda: webbrowser.open(KOFI_URL)
        )
        kofi_btn.pack(pady=10)

        # Close button
        ttk.Button(about, text="Close", command=about.destroy).pack(pady=(0, 10))

    def _update_error_label(self) -> None:
        """Update the error label visibility and text."""
        if self.error_label is None:
            return

        if self._last_error:
            self.error_label.config(text=self._last_error)
            self.error_label.pack(fill=tk.X, padx=10, pady=(5, 0))
        else:
            self.error_label.pack_forget()

    def _update_status(self) -> None:
        """Update the status label."""
        if self.status_label:
            state = self.get_state()
            self.status_label.config(text=f"Status: {state}", foreground="black")

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

        # Update error label
        self._update_error_label()

        # Update last key display
        if self.key_label and self.get_last_key:
            last_key = self.get_last_key()
            self.key_label.config(text=f"Key: {last_key or '-'}")

        # Update piano roll
        self._draw_piano_roll()

        # Schedule next update
        self._update_job = self.window.after(200, self._update_progress)

    def _draw_piano_roll(self) -> None:
        """Draw upcoming notes on the preview canvas."""
        if not self.preview_canvas or not self.get_upcoming_notes:
            return

        self.preview_canvas.delete("all")

        canvas_width = self.preview_canvas.winfo_width()
        canvas_height = self.preview_canvas.winfo_height()

        if canvas_width < 10:  # Not yet rendered
            return

        # Draw playhead line
        self.preview_canvas.create_line(2, 0, 2, canvas_height, fill="red", width=2)

        lookahead = self._lookahead
        notes = self.get_upcoming_notes(float(lookahead))

        if not notes:
            return

        # Find note range for vertical scaling
        min_note = min(n.midi_note for n in notes)
        max_note = max(n.midi_note for n in notes)
        note_range = max(max_note - min_note, 12)  # At least one octave

        current_pos = self.get_position() if self.get_position else 0.0

        for note in notes:
            # X position based on time
            time_offset = note.time - current_pos
            x = 5 + (time_offset / lookahead) * (canvas_width - 10)

            # Width based on duration (min 3px)
            width = max(3, (note.duration / lookahead) * (canvas_width - 10))

            # Y position based on pitch (higher = top)
            y_ratio = 1 - ((note.midi_note - min_note) / note_range)
            y = 5 + y_ratio * (canvas_height - 10)

            # Draw note rectangle
            self.preview_canvas.create_rectangle(
                x, y - 3, x + width, y + 3,
                fill="#4CAF50", outline="#2E7D32"
            )

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
            self.key_label = None
            self.speed_var = None
            self.speed_label = None
            self.preview_canvas = None
            self.lookahead_var = None
            self.preview_frame = None
            self.error_label = None

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
