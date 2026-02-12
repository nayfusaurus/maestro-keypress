"""Tkinter GUI for song selection.

Provides a simple window to browse and select MIDI files.
"""

import threading
import tkinter as tk
import webbrowser
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, ttk

from maestro.game_mode import GameMode
from maestro.key_layout import KeyLayout
from maestro.logger import open_log_file
from maestro.parser import get_midi_info, parse_midi

# App info
APP_VERSION = "1.2.0"
KOFI_URL = "https://ko-fi.com/nayfusaurus"

# Valid key names that can be bound (maps tkinter keysym to config key name)
BINDABLE_KEYS = {
    "F1": "f1",
    "F2": "f2",
    "F3": "f3",
    "F4": "f4",
    "F5": "f5",
    "F6": "f6",
    "F7": "f7",
    "F8": "f8",
    "F9": "f9",
    "F10": "f10",
    "F11": "f11",
    "F12": "f12",
    "Escape": "escape",
    "Home": "home",
    "End": "end",
    "Insert": "insert",
    "Delete": "delete",
    "Prior": "page_up",
    "Next": "page_down",
}


def get_songs_from_folder(folder: Path) -> list[Path]:
    """Get all MIDI files from a folder.

    Args:
        folder: Path to the songs folder

    Returns:
        List of paths to .mid and .midi files, sorted alphabetically
    """
    if not folder.exists():
        return []

    mid_files = list(folder.glob("*.mid"))
    midi_files = list(folder.glob("*.midi"))
    return sorted(mid_files + midi_files)


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
        on_folder_change: Callable[[Path], None] | None = None,
        on_layout_change: Callable[[KeyLayout], None] | None = None,
        initial_layout: KeyLayout = KeyLayout.KEYS_22,
        get_note_compatibility: Callable[[Path], tuple[int, int]] | None = None,
        on_favorite_toggle: Callable[[str, bool], None] | None = None,
        get_favorites: Callable[[], list[str]] | None = None,
        on_sharp_handling_change: Callable[[str], None] | None = None,
        initial_sharp_handling: str = "skip",
        on_hotkey_change: Callable[[str, str], None] | None = None,
        initial_play_key: str = "f2",
        initial_stop_key: str = "f3",
        initial_emergency_key: str = "escape",
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
            on_folder_change: Callback when songs folder is changed via browse
            on_layout_change: Callback when key layout is changed
            initial_layout: Initial key layout setting
            get_note_compatibility: Callback to get (playable, total) note counts for a song
            on_favorite_toggle: Callback when favorite is toggled (song_name, is_favorite)
            get_favorites: Callback to get list of favorite song names
            on_sharp_handling_change: Callback when sharp handling setting changes
            initial_sharp_handling: Initial sharp handling setting ("skip" or "snap")
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
        self.on_folder_change = on_folder_change
        self.on_layout_change = on_layout_change
        self.get_note_compatibility = get_note_compatibility
        self.on_favorite_toggle = on_favorite_toggle
        self.get_favorites = get_favorites
        self.on_sharp_handling_change = on_sharp_handling_change
        self.on_hotkey_change = on_hotkey_change
        self._key_layout = initial_layout
        self._sharp_handling = initial_sharp_handling
        self._play_key = initial_play_key
        self._stop_key = initial_stop_key
        self._emergency_key = initial_emergency_key
        self._lookahead = initial_lookahead
        self._transpose = initial_transpose
        self._show_preview = initial_show_preview

        self.window: tk.Tk | None = None
        self.song_listbox: tk.Listbox | None = None
        self.status_label: tk.Label | ttk.Label | None = None
        self.folder_label: tk.Label | ttk.Label | None = None
        self.search_var: tk.StringVar | None = None
        self.progress_bar: ttk.Progressbar | None = None
        self.progress_label: tk.Label | ttk.Label | None = None
        self.song_info_label: tk.Label | ttk.Label | None = None
        self.game_mode_var: tk.StringVar | None = None
        self.key_label: tk.Label | ttk.Label | None = None
        self.speed_var: tk.DoubleVar | None = None
        self.speed_label: tk.Label | ttk.Label | None = None
        self.preview_canvas: tk.Canvas | None = None
        self.lookahead_var: tk.IntVar | None = None
        self.preview_frame: ttk.LabelFrame | None = None
        self.layout_var: tk.StringVar | None = None
        self.layout_frame: ttk.Frame | None = None
        self.error_label: tk.Label | None = None
        self.song_detail_label: tk.Label | None = None
        self._fav_btn: ttk.Button | None = None
        self._validation_results: dict[str, str] = {}  # path_str -> "valid" | "invalid" | "pending"
        self._song_info: dict[str, dict] = {}  # path_str -> {duration, bpm, note_count}
        self._song_notes: dict[
            str, list
        ] = {}  # path_str -> list of Note objects (for compatibility)
        self._validation_cache: dict[str, tuple[float, bool]] = {}  # path_str -> (mtime, is_valid)
        self._songs: list[Path] = []
        self._filtered_songs: list[Path] = []
        self._update_job: str | None = None
        self._last_error: str = ""
        self._prev_state: str = "Stopped"
        self._flash_count: int = 0
        self._original_title: str = "Maestro - Song Picker"
        self._auto_minimized: bool = False

    def set_error(self, message: str) -> None:
        """Set error message to display in status."""
        self._last_error = message

    def _validate_songs_background(self) -> None:
        """Validate all songs in a background thread, using cache for unchanged files."""
        songs_to_validate = list(self._songs)

        # Mark all as pending initially
        for song in songs_to_validate:
            self._validation_results[str(song)] = "pending"

        def validate():
            for song in songs_to_validate:
                song_str = str(song)

                # Check if file still exists
                if not song.exists():
                    self._validation_results[song_str] = "invalid"
                    self._song_info[song_str] = {"duration": 0, "bpm": 0, "note_count": 0}
                    self._song_notes[song_str] = []
                    continue

                # Get current mtime
                try:
                    current_mtime = song.stat().st_mtime
                except OSError:
                    # File access error, mark as invalid
                    self._validation_results[song_str] = "invalid"
                    self._song_info[song_str] = {"duration": 0, "bpm": 0, "note_count": 0}
                    self._song_notes[song_str] = []
                    continue

                # Check cache
                cached_entry = self._validation_cache.get(song_str)
                if cached_entry is not None:
                    cached_mtime, cached_is_valid = cached_entry
                    if cached_mtime == current_mtime:
                        # File unchanged, reuse cached result
                        if cached_is_valid:
                            self._validation_results[song_str] = "valid"
                            # Info and notes should already be in the dicts
                        else:
                            self._validation_results[song_str] = "invalid"
                            self._song_info[song_str] = {"duration": 0, "bpm": 0, "note_count": 0}
                            self._song_notes[song_str] = []

                        # Update GUI from main thread
                        if self.window:
                            self.window.after(0, self._update_song_colors)
                        continue

                # File changed or not in cache, validate it
                try:
                    info = get_midi_info(song)
                    notes = parse_midi(song)

                    # For drums layout, check if song has notes in drum range (60-67)
                    if self._key_layout == KeyLayout.DRUMS:
                        has_drum_notes = any(60 <= note.midi_note <= 67 for note in notes)
                        if not has_drum_notes:
                            # No playable drum notes
                            self._validation_results[song_str] = "invalid"
                            self._song_info[song_str] = {"duration": 0, "bpm": 0, "note_count": 0}
                            self._song_notes[song_str] = []
                            self._validation_cache[song_str] = (current_mtime, False)
                            # Update GUI from main thread
                            if self.window:
                                self.window.after(0, self._update_song_colors)
                            continue

                    self._validation_results[song_str] = "valid"
                    self._song_info[song_str] = info
                    self._song_notes[song_str] = notes
                    self._validation_cache[song_str] = (current_mtime, True)
                except Exception:
                    self._validation_results[song_str] = "invalid"
                    self._song_info[song_str] = {"duration": 0, "bpm": 0, "note_count": 0}
                    self._song_notes[song_str] = []
                    self._validation_cache[song_str] = (current_mtime, False)

                # Update GUI from main thread
                if self.window:
                    self.window.after(0, self._update_song_colors)

        threading.Thread(target=validate, daemon=True).start()

    def _update_song_colors(self) -> None:
        """Update song list item colors based on validation status."""
        if self.song_listbox is None:
            return

        for i, song in enumerate(self._filtered_songs):
            status = self._validation_results.get(str(song), "pending")
            if status == "valid":
                self.song_listbox.itemconfig(i, foreground="green")
            elif status == "invalid":
                self.song_listbox.itemconfig(i, foreground="red")
            else:
                self.song_listbox.itemconfig(i, foreground="gray")

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
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # Menu bar
        self._create_menu_bar()

        # Folder selection
        folder_frame = ttk.Frame(self.window)
        folder_frame.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Label(folder_frame, text="Folder:").pack(side=tk.LEFT)
        ttk.Button(folder_frame, text="Browse...", command=self._on_browse_click).pack(
            side=tk.RIGHT
        )
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

        # Key layout selection (Heartopia only)
        self.layout_frame = ttk.Frame(self.window)

        ttk.Label(self.layout_frame, text="Keys:").pack(side=tk.LEFT)
        self.layout_var = tk.StringVar(value=self._key_layout.value)
        layout_dropdown = ttk.Combobox(
            self.layout_frame,
            textvariable=self.layout_var,
            values=[layout.value for layout in KeyLayout],
            state="readonly",
            width=20,
        )
        layout_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        layout_dropdown.bind("<<ComboboxSelected>>", self._on_layout_change)

        # Show/hide based on current game mode
        self._update_layout_visibility()

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
        self.song_listbox.bind("<<ListboxSelect>>", self._on_song_select)
        scrollbar.config(command=self.song_listbox.yview)

        # Control buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(btn_frame, text="Play", command=self._on_play_click).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Stop", command=self._on_stop_click).pack(side=tk.LEFT, padx=2)
        self._fav_btn = ttk.Button(
            btn_frame, text="\u2606", width=3, command=self._on_favorite_click
        )
        self._fav_btn.pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Refresh", command=self._refresh_songs).pack(
            side=tk.RIGHT, padx=2
        )

        # Song detail label (shows info for selected song)
        self.song_detail_label = tk.Label(
            self.window,
            text="Select a song to see details",
            foreground="gray",
            font=("TkDefaultFont", 9),
            wraplength=370,
            justify=tk.LEFT,
        )
        self.song_detail_label.pack(fill=tk.X, padx=10, pady=(0, 5))

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
        help_menu.add_command(label="Disclaimer", command=self._show_disclaimer)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self._show_about)

    def _show_settings(self) -> None:
        """Show the Settings dialog."""
        if self.window is None:
            return

        settings = tk.Toplevel(self.window)
        settings.title("Settings")
        settings.geometry("300x350")
        settings.resizable(False, False)
        settings.transient(self.window)
        settings.grab_set()

        # Center on parent window
        settings.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 300) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 350) // 2
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

        # Disable transpose for drums layout
        if self._key_layout == KeyLayout.DRUMS:
            transpose_cb.config(state=tk.DISABLED)

        # Show preview checkbox
        preview_var = tk.BooleanVar(value=self._show_preview)
        preview_cb = ttk.Checkbutton(
            settings,
            text="Show note preview panel",
            variable=preview_var,
            command=lambda: self._on_show_preview_toggle(preview_var.get()),
        )
        preview_cb.pack(anchor=tk.W, padx=20, pady=(0, 10))

        # Sharp handling (only relevant for 15-key layouts)
        sharp_frame = ttk.Frame(settings)
        sharp_frame.pack(anchor=tk.W, padx=20, pady=(0, 10))

        ttk.Label(sharp_frame, text="Sharp notes (15-key):").pack(side=tk.LEFT)
        sharp_var = tk.StringVar(value=self._sharp_handling)
        sharp_dropdown = ttk.Combobox(
            sharp_frame,
            textvariable=sharp_var,
            values=["skip", "snap"],
            state="readonly",
            width=8,
        )
        sharp_dropdown.pack(side=tk.LEFT, padx=(5, 0))
        sharp_dropdown.bind(
            "<<ComboboxSelected>>", lambda e: self._on_sharp_handling_toggle(sharp_var.get())
        )

        # Disable sharp handling for drums layout (chromatic, no sharps to skip/snap)
        if self._key_layout == KeyLayout.DRUMS:
            sharp_dropdown.config(state=tk.DISABLED)

        # Hotkeys section
        hotkey_frame = ttk.LabelFrame(settings, text="Hotkeys")
        hotkey_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # Play key
        play_row = ttk.Frame(hotkey_frame)
        play_row.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(play_row, text="Play:").pack(side=tk.LEFT)
        play_key_var = tk.StringVar(value=self._play_key.upper())
        play_key_label = ttk.Label(
            play_row, textvariable=play_key_var, width=12, relief="sunken", anchor="center"
        )
        play_key_label.pack(side=tk.LEFT, padx=(5, 5))

        # Stop key
        stop_row = ttk.Frame(hotkey_frame)
        stop_row.pack(fill=tk.X, padx=10, pady=5)
        ttk.Label(stop_row, text="Stop:").pack(side=tk.LEFT)
        stop_key_var = tk.StringVar(value=self._stop_key.upper())
        stop_key_label = ttk.Label(
            stop_row, textvariable=stop_key_var, width=12, relief="sunken", anchor="center"
        )
        stop_key_label.pack(side=tk.LEFT, padx=(5, 5))

        # Emergency stop key
        emergency_row = ttk.Frame(hotkey_frame)
        emergency_row.pack(fill=tk.X, padx=10, pady=(5, 10))
        ttk.Label(emergency_row, text="Emergency:").pack(side=tk.LEFT)
        emergency_key_var = tk.StringVar(value=self._emergency_key.upper())
        emergency_key_label = ttk.Label(
            emergency_row,
            textvariable=emergency_key_var,
            width=12,
            relief="sunken",
            anchor="center",
        )
        emergency_key_label.pack(side=tk.LEFT, padx=(5, 5))

        # Create a dict to pass all key vars to bind function
        key_vars = {
            "play_key": play_key_var,
            "stop_key": stop_key_var,
            "emergency_stop_key": emergency_key_var,
        }

        ttk.Button(
            play_row,
            text="Bind",
            width=5,
            command=lambda: self._start_key_bind(settings, play_key_var, "play_key", key_vars),
        ).pack(side=tk.LEFT)

        ttk.Button(
            stop_row,
            text="Bind",
            width=5,
            command=lambda: self._start_key_bind(settings, stop_key_var, "stop_key", key_vars),
        ).pack(side=tk.LEFT)

        ttk.Button(
            emergency_row,
            text="Bind",
            width=5,
            command=lambda: self._start_key_bind(
                settings, emergency_key_var, "emergency_stop_key", key_vars
            ),
        ).pack(side=tk.LEFT)

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

    def _on_favorite_click(self) -> None:
        """Toggle favorite for selected song."""
        song = self._get_selected_song()
        if song is None:
            return

        favorites = self.get_favorites() if self.get_favorites else []
        song_name = song.stem
        is_favorite = song_name in favorites

        if self.on_favorite_toggle:
            self.on_favorite_toggle(song_name, not is_favorite)

        self._update_favorite_button()
        self._apply_search_filter()

    def _update_favorite_button(self) -> None:
        """Update favorite button star based on selected song."""
        if not hasattr(self, "_fav_btn") or self._fav_btn is None:
            return
        song = self._get_selected_song()
        if song is None:
            self._fav_btn.config(text="\u2606")
            return

        favorites = self.get_favorites() if self.get_favorites else []
        if song.stem in favorites:
            self._fav_btn.config(text="\u2605")  # Filled star
        else:
            self._fav_btn.config(text="\u2606")  # Empty star

    def _on_sharp_handling_toggle(self, value: str) -> None:
        """Handle sharp handling dropdown change."""
        self._sharp_handling = value
        if self.on_sharp_handling_change:
            self.on_sharp_handling_change(value)

    def _check_hotkey_conflict(self, new_key: str, current_action: str) -> str | None:
        """Check if a key is already bound to another action.

        Args:
            new_key: The key to check (e.g., "f2")
            current_action: The action being bound (e.g., "play_key")

        Returns:
            The name of the conflicting action, or None if no conflict
        """
        if new_key == self._play_key and current_action != "play_key":
            return "Play"
        elif new_key == self._stop_key and current_action != "stop_key":
            return "Stop"
        elif new_key == self._emergency_key and current_action != "emergency_stop_key":
            return "Emergency Stop"
        return None

    def _start_key_bind(
        self,
        parent: tk.Toplevel,
        key_var: tk.StringVar,
        config_key: str,
        all_key_vars: dict[str, tk.StringVar] | None = None,
    ) -> None:
        """Start listening for a key press to bind to a hotkey.

        Args:
            parent: The settings dialog window
            key_var: The StringVar to update with the new key
            config_key: The config key being bound ("play_key", "stop_key", or "emergency_stop_key")
            all_key_vars: Dict mapping config keys to their StringVars for updating conflicts
        """
        original_value = key_var.get()
        key_var.set("Press a key...")

        def on_key(event):
            key_name = event.keysym
            if key_name in BINDABLE_KEYS:
                config_value = BINDABLE_KEYS[key_name]

                # Check for conflicts
                conflict = self._check_hotkey_conflict(config_value, config_key)
                if conflict:
                    from tkinter import messagebox

                    result = messagebox.askyesno(
                        "Hotkey Conflict",
                        f"Key {config_value.upper()} is already bound to {conflict}. Replace?",
                        parent=parent,
                    )
                    if not result:
                        # User canceled, revert
                        key_var.set(original_value)
                        parent.unbind("<Key>")
                        return "break"

                    # User confirmed replacement
                    # Clear the old binding by updating its display to show it needs rebinding
                    if all_key_vars:
                        if config_value == self._play_key:
                            all_key_vars["play_key"].set("(unbound)")
                        elif config_value == self._stop_key:
                            all_key_vars["stop_key"].set("(unbound)")
                        elif config_value == self._emergency_key:
                            all_key_vars["emergency_stop_key"].set("(unbound)")

                key_var.set(config_value.upper())

                # Update internal state
                if config_key == "play_key":
                    self._play_key = config_value
                elif config_key == "stop_key":
                    self._stop_key = config_value
                elif config_key == "emergency_stop_key":
                    self._emergency_key = config_value

                if self.on_hotkey_change:
                    self.on_hotkey_change(config_key, config_value)
            else:
                # Unsupported key, revert
                key_var.set(original_value)

            parent.unbind("<Key>")
            return "break"

        parent.bind("<Key>", on_key)

    def _on_song_finished(self) -> None:
        """Handle song playback completion."""
        if self.status_label:
            self.status_label.config(text="Status: Finished", foreground="green")
        self._flash_count = 6  # 3 flashes (on-off-on-off-on-off)
        self._flash_title()

        # Restore window if it was auto-minimized
        if self._auto_minimized and self.window:
            self.window.deiconify()
            self.window.lift()
            self._auto_minimized = False

    def _flash_title(self) -> None:
        """Flash the window title to indicate song finished."""
        if self.window is None or self._flash_count <= 0:
            if self.window:
                self.window.title(self._original_title)
            return

        self._flash_count -= 1
        if self._flash_count % 2 == 1:
            self.window.title("*** Song Finished! ***")
        else:
            self.window.title(self._original_title)

        self.window.after(500, self._flash_title)

    def _refresh_songs(self) -> None:
        """Refresh the song list from disk."""
        if self.song_listbox is None:
            return

        self._songs = get_songs_from_folder(self.songs_folder)
        self._apply_search_filter()
        self._validate_songs_background()

    def _apply_search_filter(self) -> None:
        """Apply current search filter to song list."""
        if self.song_listbox is None:
            return

        search_term = self.search_var.get().lower() if self.search_var else ""

        if search_term:
            filtered = [s for s in self._songs if search_term in s.stem.lower()]
        else:
            filtered = self._songs.copy()

        # Sort: favorites first, then valid/pending/invalid, each alphabetical
        def sort_key(song):
            favorites = self.get_favorites() if self.get_favorites else []
            is_fav = 0 if song.stem in favorites else 1
            status = self._validation_results.get(str(song), "pending")
            order = {"valid": 0, "pending": 1, "invalid": 2}
            return (is_fav, order.get(status, 1), song.stem.lower())

        self._filtered_songs = sorted(filtered, key=sort_key)

        self.song_listbox.delete(0, tk.END)
        for song in self._filtered_songs:
            self.song_listbox.insert(tk.END, song.stem)

        self._update_song_colors()

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
        index: int = selection[0]
        return self._filtered_songs[index]

    def _on_play_click(self) -> None:
        """Handle play button click."""
        self._last_error = ""
        self._update_error_label()
        song = self._get_selected_song()
        if song:
            self.on_play(song)
            self._update_status()
            if self.window:
                self.window.iconify()
                self._auto_minimized = True

    def _on_stop_click(self) -> None:
        """Handle stop button click."""
        self.on_stop()
        self._update_status()

    def _on_double_click(self, event) -> None:
        """Handle double-click on song."""
        self._on_play_click()

    def _on_song_select(self, event=None) -> None:
        """Handle song selection to show details."""
        song = self._get_selected_song()
        if song is None or self.song_detail_label is None:
            return

        info = self._song_info.get(str(song))
        status = self._validation_results.get(str(song), "pending")

        if status == "pending":
            self.song_detail_label.config(text="Validating...", foreground="gray")
        elif status == "invalid":
            self.song_detail_label.config(text="Invalid MIDI file", foreground="red")
        elif info:
            duration = info["duration"]
            minutes = int(duration // 60)
            secs = int(duration % 60)
            text = f"{minutes}:{secs:02d} | {info['bpm']} BPM | {info['note_count']} notes"

            # Add compatibility info if callback available
            if self.get_note_compatibility:
                playable, total = self.get_note_compatibility(song)
                if total > 0:
                    pct = round(playable / total * 100)
                    # Special message for drums layout
                    if self._key_layout == KeyLayout.DRUMS:
                        compat_text = f" | {pct}% playable on Drums (8-key) ({playable}/{total})"
                    else:
                        compat_text = f" | {pct}% playable ({playable}/{total})"
                    if pct < 100:
                        compat_text += f" - {total - playable} out of range"
                    text += compat_text

            self.song_detail_label.config(text=text, foreground="black")

        self._update_favorite_button()

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
            # Clear validation cache when folder changes
            self._validation_cache.clear()
            self._refresh_songs()
            if self.on_folder_change:
                self.on_folder_change(self.songs_folder)

    def _on_game_mode_change(self, event=None) -> None:
        """Handle game mode dropdown change."""
        if self.on_game_change and self.game_mode_var:
            selected = self.game_mode_var.get()
            for mode in GameMode:
                if mode.value == selected:
                    self.on_game_change(mode)
                    break
        self._update_layout_visibility()

    def _on_layout_change(self, event=None) -> None:
        """Handle key layout dropdown change."""
        if self.on_layout_change and self.layout_var:
            selected = self.layout_var.get()
            for layout in KeyLayout:
                if layout.value == selected:
                    self._key_layout = layout
                    self.on_layout_change(layout)
                    break
        # Refresh song detail to show updated compatibility
        self._on_song_select()

    def _update_layout_visibility(self) -> None:
        """Show layout dropdown only for Heartopia."""
        if self.layout_frame is None:
            return

        is_heartopia = True
        if self.game_mode_var:
            is_heartopia = self.game_mode_var.get() == GameMode.HEARTOPIA.value

        if is_heartopia:
            # Pack after game mode frame
            self.layout_frame.pack(fill=tk.X, padx=10, pady=(5, 0))
        else:
            self.layout_frame.pack_forget()

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
        about.geometry("300x270")
        about.resizable(False, False)
        about.transient(self.window)
        about.grab_set()

        # Center on parent window
        about.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 300) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 120) // 2
        about.geometry(f"+{x}+{y}")

        # Title
        ttk.Label(about, text="Maestro", font=("TkDefaultFont", 16, "bold")).pack(pady=(20, 5))

        # Version
        ttk.Label(about, text=f"Version {APP_VERSION}").pack()

        # Description
        ttk.Label(about, text="MIDI Piano Player for Games", foreground="gray").pack(pady=(5, 15))

        # Credits
        ttk.Label(about, text="Created by nayfusaurus").pack()

        # Separator
        ttk.Separator(about, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=20, pady=15)

        # Support section
        ttk.Label(about, text="Like this tool? Support development:").pack()

        # Ko-fi link button
        kofi_btn = ttk.Button(
            about, text="Buy me a coffee on Ko-fi", command=lambda: webbrowser.open(KOFI_URL)
        )
        kofi_btn.pack(pady=10)

        # Close button
        ttk.Button(about, text="Close", command=about.destroy).pack(pady=(0, 10))

    def _show_disclaimer(self) -> None:
        """Show the disclaimer dialog."""
        if self.window is None:
            return

        disclaimer = tk.Toplevel(self.window)
        disclaimer.title("Disclaimer")
        disclaimer.geometry("400x300")
        disclaimer.resizable(False, False)
        disclaimer.transient(self.window)
        disclaimer.grab_set()

        # Center on parent window
        disclaimer.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() - 400) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - 300) // 2
        disclaimer.geometry(f"+{x}+{y}")

        # Title
        ttk.Label(disclaimer, text="Disclaimer", font=("TkDefaultFont", 14, "bold")).pack(
            pady=(15, 10)
        )

        # Disclaimer text
        text_widget = tk.Text(
            disclaimer,
            wrap=tk.WORD,
            height=10,
            padx=10,
            pady=10,
            font=("TkDefaultFont", 9),
        )
        text_widget.pack(fill=tk.BOTH, expand=True, padx=15, pady=(0, 10))

        disclaimer_text = (
            "This software simulates keyboard input to interact with games. "
            "By using this tool, you acknowledge the following:\n\n"
            "1. USE AT YOUR OWN RISK. The developers are not responsible for "
            "any consequences, including but not limited to game bans or "
            "account suspensions.\n\n"
            "2. This tool is intended for personal, non-competitive use only. "
            "Using keyboard automation in games may violate the game's Terms "
            "of Service.\n\n"
            "3. Always check the game's policies regarding third-party tools "
            "and keyboard automation before use.\n\n"
            '4. This software is provided "as is" without warranty of any kind.'
        )

        text_widget.insert("1.0", disclaimer_text)
        text_widget.config(state=tk.DISABLED)  # Read-only

        # Close button
        ttk.Button(disclaimer, text="Close", command=disclaimer.destroy).pack(pady=(0, 15))

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

        # Detect song finish (PLAYING -> STOPPED transition, not user-initiated)
        current_state = self.get_state()
        if self._prev_state == "Playing" and current_state == "Stopped":
            self._on_song_finished()
        self._prev_state = current_state

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
                x, y - 3, x + width, y + 3, fill="#4CAF50", outline="#2E7D32"
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
            self.layout_var = None
            self.layout_frame = None
            self.key_label = None
            self.speed_var = None
            self.speed_label = None
            self.preview_canvas = None
            self.lookahead_var = None
            self.preview_frame = None
            self.error_label = None
            self.song_detail_label = None
            self._fav_btn = None

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
