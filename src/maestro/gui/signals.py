"""Signal definitions for GUI-backend communication."""

from PySide6.QtCore import QObject, Signal


class MaestroSignals(QObject):
    """All signals for communication between the GUI and the main coordinator.

    GUI -> Maestro signals are emitted by user actions in the GUI.
    Maestro -> GUI signals are emitted by the backend to update the GUI.
    """

    # --- GUI -> Maestro (user actions) ---
    play_requested = Signal(object)  # Path
    stop_requested = Signal()
    exit_requested = Signal()
    game_mode_changed = Signal(str)  # GameMode.value string
    folder_changed = Signal(object)  # Path
    layout_changed = Signal(str)  # KeyLayout.value string
    speed_changed = Signal(float)
    lookahead_changed = Signal(int)
    transpose_changed = Signal(bool)
    show_preview_changed = Signal(bool)
    favorite_toggled = Signal(str, bool)  # song_name, is_favorite
    sharp_handling_changed = Signal(str)  # "skip" or "snap"
    wwm_layout_changed = Signal(str)  # WwmLayout.value string
    hotkey_changed = Signal(str, str)  # config_key, key_name
    theme_changed = Signal(str)  # "dark" or "light"
    countdown_delay_changed = Signal(int)  # 0-10 seconds
    note_compatibility_requested = Signal(object)  # Path
    import_requested = Signal(str, bool)  # URL string, isolate_piano

    # --- Maestro -> GUI (state pushes) ---
    state_updated = Signal(str)  # Playback state string
    position_updated = Signal(float, float)  # position, duration
    current_song_updated = Signal(str)  # Song name or ""
    last_key_updated = Signal(str)  # Last key pressed
    upcoming_notes_updated = Signal(list)  # List of Note objects
    note_compatibility_result = Signal(int, int)  # playable, total
    error_occurred = Signal(str)  # Error message
    song_finished = Signal()  # Playback naturally completed
    countdown_tick = Signal(int)  # Countdown number (3, 2, 1, 0)
    favorites_loaded = Signal(list)  # List[str] of favorite names

    # Import signals (Maestro -> GUI)
    import_progress = Signal(str)  # Progress text from ImportWorker
    import_finished = Signal(str)  # Filename of imported MIDI
    import_error = Signal(str)  # Error message from import pipeline
