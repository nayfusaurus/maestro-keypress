"""Main application window composing all GUI widgets."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from maestro.game_mode import GameMode
from maestro.gui.about_dialog import AboutDialog, DisclaimerDialog
from maestro.gui.constants import APP_VERSION, BINDABLE_KEYS_QT, GITHUB_REPO
from maestro.gui.controls_panel import ControlsPanel
from maestro.gui.import_panel import ImportPanel
from maestro.gui.piano_roll import PianoRollWidget
from maestro.gui.progress_panel import NowPlayingPanel
from maestro.gui.signals import MaestroSignals
from maestro.gui.song_list import SongListWidget
from maestro.gui.theme import apply_theme
from maestro.gui.update_banner import UpdateBanner
from maestro.gui.utils import check_hotkey_conflict
from maestro.gui.workers import UpdateCheckWorker, ValidationWorker
from maestro.key_layout import KeyLayout
from maestro.logger import open_log_file
from maestro.update_checker import check_for_updates


class MainWindow(QMainWindow):
    """Main application window for Maestro song picker."""

    def __init__(
        self,
        songs_folder: Path,
        config: dict,
    ) -> None:
        super().__init__()

        self.signals = MaestroSignals()

        self.songs_folder = songs_folder
        self._config = config

        # Restore settings from config
        self._key_layout = KeyLayout.KEYS_22
        layout_str = config.get("key_layout", "22-key (Full)")
        for layout in KeyLayout:
            if layout.value == layout_str:
                self._key_layout = layout
                break

        self._sharp_handling = config.get("sharp_handling", "skip")
        self._play_key = config.get("play_key", "f2")
        self._stop_key = config.get("stop_key", "f3")
        self._emergency_key = config.get("emergency_stop_key", "escape")
        self._lookahead = config.get("preview_lookahead", 5)
        self._transpose = config.get("transpose", False)
        self._show_preview = config.get("show_preview", False)

        # Hotkey binding state
        self._listening_for: str | None = None

        # State
        self._validation_results: dict[str, str] = {}
        self._song_info: dict[str, dict] = {}
        self._song_notes: dict[str, list] = {}
        self._validation_cache: dict[str, tuple[float, bool]] = {}
        self._last_error: str = ""
        self._prev_state: str = "Stopped"
        self._flash_count: int = 0
        self._original_title: str = "Maestro - Song Picker"
        self._auto_minimized: bool = False
        self._validation_worker: ValidationWorker | None = None
        self._update_worker: UpdateCheckWorker | None = None

        self._setup_window()
        self._create_menu_bar()
        self._create_ui()
        self._connect_internal_signals()

        # Load songs and start validation
        self._refresh_songs()

        # Check for updates in background
        self._background_update_check()

    def _setup_window(self) -> None:
        """Configure the main window properties."""
        self.setWindowTitle(self._original_title)

        # Size to 80% of screen, minimum 900x600
        self.setMinimumSize(900, 600)
        primary = QApplication.primaryScreen()
        if primary is None:
            self.resize(900, 600)
            return
        screen = primary.availableGeometry()
        width = int(screen.width() * 0.8)
        height = int(screen.height() * 0.8)
        self.resize(width, height)

        # Center on screen
        self.move(
            screen.x() + (screen.width() - width) // 2,
            screen.y() + (screen.height() - height) // 2,
        )

        # Set window icon
        try:
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception:
            pass

    def _create_menu_bar(self) -> None:
        """Create the File and Help menus."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")
        file_menu.addAction("Open Log", self._on_open_log_click)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)

        # Help menu
        help_menu = menubar.addMenu("Help")
        help_menu.addAction("Check for Updates...", self._manual_update_check)
        help_menu.addSeparator()
        help_menu.addAction("Disclaimer", self._show_disclaimer)
        help_menu.addSeparator()
        help_menu.addAction("About", self._show_about)

    def _create_ui(self) -> None:
        """Build the main UI with a two-column layout (sidebar + main area)."""
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QVBoxLayout(central)
        root_layout.setSpacing(0)
        root_layout.setContentsMargins(0, 0, 0, 0)

        # Update banner (hidden by default, spans full width)
        self._update_banner = UpdateBanner()
        root_layout.addWidget(self._update_banner)

        # Two-column layout
        columns = QHBoxLayout()
        columns.setSpacing(0)
        columns.setContentsMargins(0, 0, 0, 0)

        # ── Left Column: Sidebar (fixed 320px, scrollable) ────────────

        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setFixedWidth(480)
        sidebar_scroll.setFrameShape(QFrame.Shape.NoFrame)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        sidebar_content = QWidget()
        sidebar_layout = QVBoxLayout(sidebar_content)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(12)

        self._create_transport_card(sidebar_layout)
        self._create_settings_card(sidebar_layout)

        sidebar_layout.addStretch()
        sidebar_scroll.setWidget(sidebar_content)

        columns.addWidget(sidebar_scroll)

        # ── Right Column: Main Area ───────────────────────────────────

        main_area = QWidget()
        main_area_layout = QVBoxLayout(main_area)
        main_area_layout.setContentsMargins(16, 12, 12, 12)
        main_area_layout.setSpacing(10)

        # Import panel (compact bar)
        self._import_panel = ImportPanel()
        main_area_layout.addWidget(self._import_panel)

        # Search bar
        self._search_entry = QLineEdit()
        self._search_entry.setPlaceholderText("Filter songs...")
        self._search_entry.textChanged.connect(self._on_search_change)
        main_area_layout.addWidget(self._search_entry)

        # Song list (takes majority of space)
        self._song_list = SongListWidget()
        self._song_list.song_selected.connect(self._on_song_select)
        self._song_list.song_double_clicked.connect(self._on_double_click)
        main_area_layout.addWidget(self._song_list, stretch=1)

        columns.addWidget(main_area, stretch=1)

        root_layout.addLayout(columns, stretch=1)

    # ── Sidebar Cards ─────────────────────────────────────────────────

    def _create_settings_card(self, parent_layout: QVBoxLayout) -> None:
        """Create the unified settings card (folder, game, keys, speed, options, hotkeys)."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        # ── Folder row ─────────────────────────────────────────────
        folder_row = QHBoxLayout()
        folder_row.setSpacing(6)
        self._folder_label = QLabel(str(self.songs_folder))
        self._folder_label.setProperty("class", "caption")
        self._folder_label.setToolTip(str(self.songs_folder))
        folder_row.addWidget(self._folder_label, stretch=1)
        browse_btn = QPushButton("Browse")
        browse_btn.setProperty("class", "ghost")
        browse_btn.clicked.connect(self._on_browse_click)
        folder_row.addWidget(browse_btn)
        layout.addLayout(folder_row)

        # ── Separator ──────────────────────────────────────────────
        sep0 = QFrame()
        sep0.setFrameShape(QFrame.Shape.HLine)
        sep0.setProperty("class", "separator")
        layout.addWidget(sep0)

        # ── Game mode (inline label + combo) ───────────────────────
        game_row = QHBoxLayout()
        game_row.setSpacing(8)
        game_lbl = QLabel("Game")
        game_lbl.setProperty("class", "section-heading")
        game_row.addWidget(game_lbl)
        game_row.addStretch()
        self._game_combo = QComboBox()
        self._game_combo.addItems([mode.value for mode in GameMode])
        game_mode_str = self._config.get("game_mode", GameMode.HEARTOPIA.value)
        self._game_combo.setCurrentText(game_mode_str)
        self._game_combo.currentTextChanged.connect(self._on_game_mode_change)
        game_row.addWidget(self._game_combo)
        layout.addLayout(game_row)

        # ── Key layout (Heartopia only, inline) ────────────────────
        self._layout_row = QWidget()
        layout_row_inner = QHBoxLayout(self._layout_row)
        layout_row_inner.setContentsMargins(0, 0, 0, 0)
        layout_row_inner.setSpacing(8)
        keys_lbl = QLabel("Keys")
        keys_lbl.setProperty("class", "section-heading")
        layout_row_inner.addWidget(keys_lbl)
        layout_row_inner.addStretch()
        self._layout_combo = QComboBox()
        self._layout_combo.addItems([kl.value for kl in KeyLayout])
        self._layout_combo.setCurrentText(self._key_layout.value)
        self._layout_combo.currentTextChanged.connect(self._on_layout_change)
        layout_row_inner.addWidget(self._layout_combo)
        layout.addWidget(self._layout_row)
        self._update_layout_visibility()

        # ── Speed (inline label + slider + value) ──────────────────
        speed_row = QHBoxLayout()
        speed_row.setSpacing(8)
        speed_lbl = QLabel("Speed")
        speed_lbl.setProperty("class", "section-heading")
        speed_row.addWidget(speed_lbl)
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(25, 150)
        speed_val = self._config.get("speed", 1.0)
        self._speed_slider.setValue(int(speed_val * 100))
        self._speed_slider.valueChanged.connect(self._on_speed_change)
        speed_row.addWidget(self._speed_slider, stretch=1)
        self._speed_label = QLabel(f"{speed_val:.2f}x")
        self._speed_label.setFixedWidth(48)
        speed_row.addWidget(self._speed_label)
        layout.addLayout(speed_row)

        # ── Separator ──────────────────────────────────────────────
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setProperty("class", "separator")
        layout.addWidget(sep1)

        # ── Options ────────────────────────────────────────────────
        self._transpose_cb = QCheckBox("Transpose to range")
        self._transpose_cb.setChecked(self._transpose)
        self._transpose_cb.stateChanged.connect(
            lambda state: self._on_transpose_toggle(state == Qt.CheckState.Checked.value)
        )
        layout.addWidget(self._transpose_cb)

        self._preview_cb = QCheckBox("Note preview")
        self._preview_cb.setChecked(self._show_preview)
        self._preview_cb.stateChanged.connect(
            lambda state: self._on_show_preview_toggle(
                state == Qt.CheckState.Checked.value
            )
        )
        layout.addWidget(self._preview_cb)

        # Sharp handling (inline, 15-key only)
        self._sharp_row = QWidget()
        sharp_inner = QHBoxLayout(self._sharp_row)
        sharp_inner.setContentsMargins(0, 0, 0, 0)
        sharp_inner.setSpacing(8)
        sharp_lbl = QLabel("Sharps")
        sharp_lbl.setProperty("class", "section-heading")
        sharp_inner.addWidget(sharp_lbl)
        sharp_inner.addStretch()
        self._sharp_combo = QComboBox()
        self._sharp_combo.addItems(["skip", "snap"])
        self._sharp_combo.setCurrentText(self._sharp_handling)
        self._sharp_combo.currentTextChanged.connect(self._on_sharp_handling_change)
        sharp_inner.addWidget(self._sharp_combo)
        layout.addWidget(self._sharp_row)

        # ── Separator ──────────────────────────────────────────────
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setProperty("class", "separator")
        layout.addWidget(sep2)

        # ── Appearance (inline theme toggle) ───────────────────────
        theme_row = QHBoxLayout()
        theme_row.setSpacing(8)
        theme_lbl = QLabel("Theme")
        theme_lbl.setProperty("class", "section-heading")
        theme_row.addWidget(theme_lbl)
        theme_row.addStretch()
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        theme_str = self._config.get("theme", "dark")
        self._theme_combo.setCurrentText(theme_str.capitalize())
        self._theme_combo.currentTextChanged.connect(self._on_theme_change)
        theme_row.addWidget(self._theme_combo)
        layout.addLayout(theme_row)

        # ── Separator ──────────────────────────────────────────────
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        sep3.setProperty("class", "separator")
        layout.addWidget(sep3)

        # ── Hotkeys (compact grid) ────────────────────────────────
        hotkey_heading = QLabel("Hotkeys")
        hotkey_heading.setProperty("class", "section-heading")
        layout.addWidget(hotkey_heading)

        # Play key row
        play_row = QHBoxLayout()
        play_row.setSpacing(6)
        play_action_lbl = QLabel("Play")
        play_action_lbl.setProperty("class", "caption")
        play_action_lbl.setFixedWidth(60)
        play_row.addWidget(play_action_lbl)
        self._hotkey_play_label = QLabel(self._play_key.upper())
        self._hotkey_play_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hotkey_play_label.setMinimumWidth(80)
        self._hotkey_play_label.setProperty("class", "key-badge")
        play_row.addWidget(self._hotkey_play_label)
        play_bind = QPushButton("Bind")
        play_bind.setFixedWidth(44)
        play_bind.setProperty("class", "ghost")
        play_bind.clicked.connect(lambda: self._start_key_bind("play_key"))
        play_row.addWidget(play_bind)
        play_row.addStretch()
        layout.addLayout(play_row)

        # Stop key row
        stop_row = QHBoxLayout()
        stop_row.setSpacing(6)
        stop_action_lbl = QLabel("Stop")
        stop_action_lbl.setProperty("class", "caption")
        stop_action_lbl.setFixedWidth(60)
        stop_row.addWidget(stop_action_lbl)
        self._hotkey_stop_label = QLabel(self._stop_key.upper())
        self._hotkey_stop_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hotkey_stop_label.setMinimumWidth(80)
        self._hotkey_stop_label.setProperty("class", "key-badge")
        stop_row.addWidget(self._hotkey_stop_label)
        stop_bind = QPushButton("Bind")
        stop_bind.setFixedWidth(44)
        stop_bind.setProperty("class", "ghost")
        stop_bind.clicked.connect(lambda: self._start_key_bind("stop_key"))
        stop_row.addWidget(stop_bind)
        stop_row.addStretch()
        layout.addLayout(stop_row)

        # Emergency stop key row
        emerg_row = QHBoxLayout()
        emerg_row.setSpacing(6)
        emerg_action_lbl = QLabel("Panic")
        emerg_action_lbl.setProperty("class", "caption")
        emerg_action_lbl.setFixedWidth(60)
        emerg_row.addWidget(emerg_action_lbl)
        self._hotkey_emergency_label = QLabel(self._emergency_key.upper())
        self._hotkey_emergency_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hotkey_emergency_label.setMinimumWidth(80)
        self._hotkey_emergency_label.setProperty("class", "key-badge")
        emerg_row.addWidget(self._hotkey_emergency_label)
        emerg_bind = QPushButton("Bind")
        emerg_bind.setFixedWidth(44)
        emerg_bind.setProperty("class", "ghost")
        emerg_bind.clicked.connect(lambda: self._start_key_bind("emergency_stop_key"))
        emerg_row.addWidget(emerg_bind)
        emerg_row.addStretch()
        layout.addLayout(emerg_row)

        # ── Separator ──────────────────────────────────────────────
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.Shape.HLine)
        sep4.setProperty("class", "separator")
        layout.addWidget(sep4)

        # ── Piano Isolation ────────────────────────────────────────
        demucs_row = QHBoxLayout()
        demucs_row.setSpacing(8)
        demucs_available = self._check_demucs_available()
        self._demucs_status = QLabel(
            "Piano model installed" if demucs_available else "Piano model not installed"
        )
        self._demucs_status.setProperty("class", "caption")
        if demucs_available:
            self._demucs_status.setProperty("state", "finished")
        demucs_row.addWidget(self._demucs_status, stretch=1)
        self._demucs_btn = QPushButton(
            "Remove" if demucs_available else "Download"
        )
        self._demucs_btn.setProperty("class", "ghost")
        self._demucs_btn.clicked.connect(self._on_demucs_btn_click)
        demucs_row.addWidget(self._demucs_btn)
        layout.addLayout(demucs_row)

        # Update options state based on current layout
        self._update_options_state()

        parent_layout.addWidget(card)

    def _create_transport_card(self, parent_layout: QVBoxLayout) -> None:
        """Create the transport card — focal point of the sidebar."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(8)

        # Error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setProperty("state", "error")
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        card_layout.addWidget(self._error_label)

        # Now Playing panel
        self._now_playing = NowPlayingPanel()
        card_layout.addWidget(self._now_playing)

        # Control buttons
        self._controls = ControlsPanel()
        card_layout.addWidget(self._controls)

        # Status row — compact, dimmed
        status_row = QHBoxLayout()
        status_row.setSpacing(4)
        self._status_label = QLabel("Stopped")
        self._status_label.setProperty("class", "caption")
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        self._key_label = QLabel("")
        self._key_label.setProperty("class", "caption")
        status_row.addWidget(self._key_label)
        card_layout.addLayout(status_row)

        # Note Preview panel (conditionally shown)
        self._preview_container = QWidget()
        preview_layout = QVBoxLayout(self._preview_container)
        preview_layout.setContentsMargins(0, 4, 0, 0)
        preview_layout.setSpacing(4)

        # Lookahead selector
        lookahead_row = QHBoxLayout()
        lookahead_row.setSpacing(4)
        lookahead_lbl = QLabel("Lookahead")
        lookahead_lbl.setProperty("class", "caption")
        lookahead_row.addWidget(lookahead_lbl)
        self._lookahead_combo = QComboBox()
        self._lookahead_combo.addItems(["2", "5", "10"])
        self._lookahead_combo.setCurrentText(str(self._lookahead))
        self._lookahead_combo.currentTextChanged.connect(self._on_lookahead_change)
        lookahead_row.addWidget(self._lookahead_combo)
        sec_lbl = QLabel("sec")
        sec_lbl.setProperty("class", "caption")
        lookahead_row.addWidget(sec_lbl)
        lookahead_row.addStretch()
        preview_layout.addLayout(lookahead_row)

        # Piano roll canvas
        self._piano_roll = PianoRollWidget()
        preview_layout.addWidget(self._piano_roll)

        card_layout.addWidget(self._preview_container)
        self._preview_container.setVisible(self._show_preview)

        parent_layout.addWidget(card)

    # ── Signal Connections ────────────────────────────────────────────

    def _connect_internal_signals(self) -> None:
        """Connect internal widget signals to MainWindow methods and MaestroSignals."""
        # Controls panel
        self._controls.play_clicked.connect(self._on_play_click)
        self._controls.stop_clicked.connect(self._on_stop_click)
        self._controls.favorite_clicked.connect(self._on_favorite_click)
        self._controls.refresh_clicked.connect(self._refresh_songs)

        # Backend -> GUI state updates
        self.signals.state_updated.connect(self._on_state_updated)
        self.signals.position_updated.connect(self._on_position_updated)
        self.signals.current_song_updated.connect(self._now_playing.update_song)
        self.signals.last_key_updated.connect(self._on_last_key_updated)
        self.signals.upcoming_notes_updated.connect(self._on_upcoming_notes_updated)
        self.signals.note_compatibility_result.connect(self._on_note_compatibility_result)
        self.signals.error_occurred.connect(self._on_error)
        self.signals.song_finished.connect(self._on_song_finished)
        self.signals.countdown_tick.connect(self._on_countdown_tick)
        self.signals.favorites_loaded.connect(self._on_favorites_loaded)

        # Import panel
        self._import_panel.import_clicked.connect(self._on_import_request)
        self.signals.import_progress.connect(self._import_panel.show_progress)
        self.signals.import_finished.connect(self._on_import_finished)
        self.signals.import_error.connect(self._import_panel.show_error)

    # --- State update handlers ---

    def _on_state_updated(self, state: str) -> None:
        """Handle playback state update from backend."""
        self._status_label.setText(state)
        if state == "Finished":
            self._status_label.setProperty("state", "finished")
        else:
            self._status_label.setProperty("state", "")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)

        # Detect song finish
        if self._prev_state == "Playing" and state == "Stopped":
            self._on_song_finished()
        self._prev_state = state

    def _on_position_updated(self, position: float, duration: float) -> None:
        """Handle position update from backend."""
        self._now_playing.update_progress(position, duration)

    def _on_last_key_updated(self, key: str) -> None:
        """Handle last key update from backend."""
        self._key_label.setText(key.upper() if key else "")

    def _on_upcoming_notes_updated(self, notes: list) -> None:
        """Handle upcoming notes update from backend."""
        self._piano_roll.set_notes(notes, self._current_position, float(self._lookahead))

    def _on_note_compatibility_result(self, playable: int, total: int) -> None:
        """Handle note compatibility result — update the song item directly."""
        song = self._song_list.get_selected_song()
        if song:
            self._song_list.update_song_compatibility(str(song), playable, total)

    def _on_error(self, message: str) -> None:
        """Display an error message."""
        self._last_error = message
        self._update_error_label()

    def _on_countdown_tick(self, count: int) -> None:
        """Handle countdown tick from backend."""
        if count > 0:
            self._status_label.setText(f"Starting in {count}...")
        else:
            self._status_label.setText("Playing")

    def _on_favorites_loaded(self, favorites: list) -> None:
        """Handle favorites list loaded from backend."""
        self._favorites = favorites
        self._apply_search_filter()

    # --- Song finish handling ---

    def _on_song_finished(self) -> None:
        """Handle song playback completion."""
        self._status_label.setText("Finished")
        self._status_label.setProperty("state", "finished")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
        self._flash_count = 6
        self._flash_title()

        # Restore window if it was auto-minimized
        if self._auto_minimized:
            self.showNormal()
            self.raise_()
            self.activateWindow()
            self._auto_minimized = False

    def _flash_title(self) -> None:
        """Flash the window title to indicate song finished."""
        if self._flash_count <= 0:
            self.setWindowTitle(self._original_title)
            return

        self._flash_count -= 1
        if self._flash_count % 2 == 1:
            self.setWindowTitle("*** Song Finished! ***")
        else:
            self.setWindowTitle(self._original_title)

        QTimer.singleShot(500, self._flash_title)

    # --- User action handlers ---

    def _should_auto_minimize(self) -> bool:
        """Check if auto-minimize should be applied.

        Returns False when the app is on a secondary monitor.
        """
        screens = QApplication.screens()
        if len(screens) <= 1:
            return True
        window_screen = self.screen()
        primary_screen = QApplication.primaryScreen()
        return window_screen == primary_screen

    def _on_play_click(self) -> None:
        """Handle play button click."""
        self._last_error = ""
        self._update_error_label()
        song = self._song_list.get_selected_song()
        if song:
            self.signals.play_requested.emit(song)
            if self._should_auto_minimize():
                self.showMinimized()
                self._auto_minimized = True

    def _on_stop_click(self) -> None:
        """Handle stop button click."""
        self.signals.stop_requested.emit()

    def _on_double_click(self, song) -> None:
        """Handle double-click on song."""
        self._on_play_click()

    def _on_song_select(self, song) -> None:
        """Handle song selection — request compatibility for valid songs."""
        if song is None:
            return

        status = self._validation_results.get(str(song), "pending")
        if status == "valid":
            self.signals.note_compatibility_requested.emit(song)

        self._update_favorite_button()

    def _on_favorite_click(self) -> None:
        """Toggle favorite for selected song."""
        song = self._song_list.get_selected_song()
        if song is None:
            return

        favorites = getattr(self, "_favorites", [])
        song_name = song.stem
        is_favorite = song_name in favorites

        self.signals.favorite_toggled.emit(song_name, not is_favorite)

        # Update local state optimistically
        if is_favorite:
            self._favorites = [f for f in favorites if f != song_name]
        else:
            self._favorites = favorites + [song_name]

        self._update_favorite_button()
        self._apply_search_filter()

    def _on_import_request(self, url: str, isolate: bool) -> None:
        """Handle import button click from ImportPanel."""
        self._import_panel.set_importing(True)
        self.signals.import_requested.emit(url, isolate)

    def _on_import_finished(self, filename: str) -> None:
        """Handle successful import completion."""
        self._import_panel.set_importing(False)
        self._import_panel.show_success(f"Downloaded: {filename}")
        self._refresh_songs()

    def _update_favorite_button(self) -> None:
        """Update favorite button star based on selected song."""
        song = self._song_list.get_selected_song()
        if song is None:
            self._controls.set_favorite(False)
            return

        favorites = getattr(self, "_favorites", [])
        self._controls.set_favorite(song.stem in favorites)

    def _on_browse_click(self) -> None:
        """Handle browse button click."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Songs Folder", str(self.songs_folder)
        )
        if folder:
            self.songs_folder = Path(folder)
            self._folder_label.setText(str(self.songs_folder))
            self._validation_cache.clear()
            self._refresh_songs()
            self.signals.folder_changed.emit(self.songs_folder)

    def _on_game_mode_change(self, selected: str) -> None:
        """Handle game mode dropdown change."""
        self.signals.game_mode_changed.emit(selected)
        self._update_layout_visibility()
        self._update_options_state()

    def _on_layout_change(self, selected: str) -> None:
        """Handle key layout dropdown change."""
        for layout in KeyLayout:
            if layout.value == selected:
                self._key_layout = layout
                break
        self.signals.layout_changed.emit(selected)
        self._update_options_state()
        # Refresh song detail to show updated compatibility
        self._on_song_select(self._song_list.get_selected_song())

    def _update_layout_visibility(self) -> None:
        """Show layout dropdown only for Heartopia."""
        is_heartopia = self._game_combo.currentText() == GameMode.HEARTOPIA.value
        self._layout_row.setVisible(is_heartopia)

    def _update_options_state(self) -> None:
        """Enable/disable options based on current layout and game mode."""
        is_drums = self._key_layout == KeyLayout.DRUMS
        is_xylophone = self._key_layout == KeyLayout.XYLOPHONE
        no_transpose = is_drums or is_xylophone

        self._transpose_cb.setEnabled(not no_transpose)
        self._sharp_combo.setEnabled(not no_transpose)

        # Sharp handling only relevant for 15-key layouts
        is_15_key = self._key_layout in (KeyLayout.KEYS_15_DOUBLE, KeyLayout.KEYS_15_TRIPLE)
        self._sharp_row.setVisible(is_15_key)

    def _on_speed_change(self, value: int) -> None:
        """Handle speed slider change."""
        speed = value / 100.0
        self._speed_label.setText(f"{speed:.2f}x")
        self.signals.speed_changed.emit(speed)

    def _on_search_change(self, text: str) -> None:
        """Handle search text change."""
        self._apply_search_filter()

    def _on_lookahead_change(self, text: str) -> None:
        """Handle lookahead dropdown change."""
        try:
            self._lookahead = int(text)
        except ValueError:
            return
        self.signals.lookahead_changed.emit(self._lookahead)

    # --- Options handlers ---

    def _on_transpose_toggle(self, value: bool) -> None:
        """Handle transpose checkbox toggle."""
        self._transpose = value
        self.signals.transpose_changed.emit(value)

    def _on_show_preview_toggle(self, value: bool) -> None:
        """Handle show preview checkbox toggle."""
        self._show_preview = value
        self._preview_container.setVisible(value)
        self.signals.show_preview_changed.emit(value)

    def _on_sharp_handling_change(self, value: str) -> None:
        """Handle sharp handling dropdown change."""
        self._sharp_handling = value
        self.signals.sharp_handling_changed.emit(value)

    def _on_theme_change(self, selected: str) -> None:
        """Handle theme dropdown change."""
        dark = selected == "Dark"
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, dark=dark)
        self.signals.theme_changed.emit("dark" if dark else "light")

    # --- Hotkey binding ---

    def _get_key_label(self, config_key: str) -> QLabel:
        """Get the key display label for a config key."""
        if config_key == "play_key":
            return self._hotkey_play_label
        elif config_key == "stop_key":
            return self._hotkey_stop_label
        return self._hotkey_emergency_label

    def _start_key_bind(self, config_key: str) -> None:
        """Enter key-binding mode for the specified action."""
        self._listening_for = config_key
        label = self._get_key_label(config_key)
        label.setText("Press a key...")
        self.grabKeyboard()

    def keyPressEvent(self, event) -> None:  # noqa: N802
        """Handle key press for hotkey binding."""
        if self._listening_for is None:
            super().keyPressEvent(event)
            return

        # Release keyboard grab immediately so dialogs can receive input
        self.releaseKeyboard()

        qt_key = event.key()
        config_key = self._listening_for
        label = self._get_key_label(config_key)

        config_value = BINDABLE_KEYS_QT.get(qt_key)
        if config_value is None:
            # Unsupported key — revert
            current = getattr(self, f"_{config_key}", "")
            label.setText(current.upper() if current else "")
            self._listening_for = None
            return

        # Check for conflicts
        conflict = check_hotkey_conflict(
            config_value, config_key,
            self._play_key, self._stop_key, self._emergency_key,
        )
        if conflict:
            result = QMessageBox.question(
                self,
                "Hotkey Conflict",
                f"Key {config_value.upper()} is already bound to {conflict}. Replace?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if result != QMessageBox.StandardButton.Yes:
                current = getattr(self, f"_{config_key}", "")
                label.setText(current.upper() if current else "")
                self._listening_for = None
                return

            # Clear the conflicting binding's display
            if config_value == self._play_key:
                self._hotkey_play_label.setText("(unbound)")
            elif config_value == self._stop_key:
                self._hotkey_stop_label.setText("(unbound)")
            elif config_value == self._emergency_key:
                self._hotkey_emergency_label.setText("(unbound)")

        label.setText(config_value.upper())

        # Update internal state
        if config_key == "play_key":
            self._play_key = config_value
        elif config_key == "stop_key":
            self._stop_key = config_value
        elif config_key == "emergency_stop_key":
            self._emergency_key = config_value

        self.signals.hotkey_changed.emit(config_key, config_value)
        self._listening_for = None

    # --- Song management ---

    def _refresh_songs(self) -> None:
        """Refresh the song list from disk."""
        self._song_list.load_songs(self.songs_folder)

        # Mark all as pending
        for song in self._song_list.get_songs():
            self._validation_results[str(song)] = "pending"

        self._apply_search_filter()
        self._start_validation()

    def _apply_search_filter(self) -> None:
        """Apply current search filter to song list."""
        search_term = self._search_entry.text() if self._search_entry else ""
        favorites = getattr(self, "_favorites", [])
        self._song_list.apply_filter(search_term, favorites, self._validation_results)

    def _start_validation(self) -> None:
        """Start background MIDI validation."""
        songs = self._song_list.get_songs()
        if not songs:
            return

        self._validation_worker = ValidationWorker(
            songs=songs,
            key_layout=self._key_layout,
            game_mode=self._game_combo.currentText(),
            transpose=self._transpose,
            sharp_handling=self._sharp_handling,
            validation_cache=self._validation_cache,
            song_info=self._song_info,
            song_notes=self._song_notes,
        )
        self._validation_worker.song_validated.connect(self._on_song_validated)
        self._validation_worker.validation_finished.connect(self._on_validation_finished)
        self._validation_worker.start()

    def _on_song_validated(
        self, path_str: str, status: str, info: dict, notes: list, playable: int, total: int
    ) -> None:
        """Handle validation result for a single song."""
        self._validation_results[path_str] = status
        self._song_info[path_str] = info
        self._song_notes[path_str] = notes
        self._song_list.on_song_validated(path_str, status, info, notes)
        if status == "valid" and total > 0:
            self._song_list.update_song_compatibility(path_str, playable, total)

    def _on_validation_finished(self) -> None:
        """Handle validation completion."""
        self._apply_search_filter()

    # --- Update checking ---

    def _background_update_check(self) -> None:
        """Check for updates in a background thread."""
        self._update_worker = UpdateCheckWorker(APP_VERSION, GITHUB_REPO, timeout=5)
        self._update_worker.update_result.connect(self._on_update_check_result)
        self._update_worker.start()

    def _on_update_check_result(self, update_info) -> None:
        """Handle background update check result."""
        if update_info.has_update:
            self._update_banner.show_update(update_info)

    def _manual_update_check(self) -> None:
        """Manually check for updates (from menu)."""
        self.setCursor(Qt.CursorShape.WaitCursor)
        update_info = check_for_updates(APP_VERSION, GITHUB_REPO, timeout=10)
        self.unsetCursor()

        if update_info.error:
            QMessageBox.warning(
                self,
                "Update Check Failed",
                f"Could not check for updates.\n\n{update_info.error}",
            )
        elif update_info.has_update:
            self._update_banner.show_update(update_info)
        else:
            QMessageBox.information(
                self,
                "No Updates Available",
                f"You're up to date! (v{APP_VERSION})",
            )

    # --- Error handling ---

    def _update_error_label(self) -> None:
        """Update the error label visibility and text."""
        if self._last_error:
            self._error_label.setText(self._last_error)
            self._error_label.setVisible(True)
        else:
            self._error_label.setVisible(False)

    def set_error(self, message: str) -> None:
        """Set error message to display in status."""
        self._last_error = message
        self._update_error_label()

    # --- Helpers ---

    def _check_demucs_available(self) -> bool:
        """Check if the demucs model is installed."""
        try:
            from maestro.importers.youtube import is_demucs_available

            model_dir = Path.home() / ".maestro" / "models" / "htdemucs"
            return is_demucs_available(model_dir)
        except Exception:
            return False

    def _on_demucs_btn_click(self) -> None:
        """Handle Download/Remove Model button click."""
        import logging
        import shutil

        logger = logging.getLogger("maestro")
        model_dir = Path.home() / ".maestro" / "models" / "htdemucs"

        if self._check_demucs_available():
            # Remove the model
            logger.info("Removing demucs model from %s", model_dir)
            try:
                shutil.rmtree(model_dir)
                logger.info("Demucs model removed")
            except Exception as e:
                logger.error("Failed to remove demucs model: %s", e)
                self.set_error(f"Failed to remove model: {e}")
                return
            self._update_demucs_ui(installed=False)
        else:
            # Download the model
            logger.info("Starting demucs model download to %s", model_dir)
            self._demucs_btn.setEnabled(False)
            self._demucs_btn.setText("Downloading...")
            self._demucs_status.setText("Downloading...")
            self._demucs_status.setProperty("state", "")
            self._demucs_status.style().unpolish(self._demucs_status)
            self._demucs_status.style().polish(self._demucs_status)

            from maestro.gui.workers import DemucsDownloadWorker

            self._demucs_worker = DemucsDownloadWorker(model_dir)
            self._demucs_worker.progress.connect(self._on_demucs_progress)
            self._demucs_worker.finished.connect(self._on_demucs_finished)
            self._demucs_worker.error.connect(self._on_demucs_error)
            self._demucs_worker.start()

    def _on_demucs_progress(self, text: str) -> None:
        """Handle demucs download progress updates."""
        self._demucs_status.setText(text)

    def _on_demucs_finished(self) -> None:
        """Handle successful demucs model download."""
        import logging

        logging.getLogger("maestro").info("Demucs model download complete")
        self._update_demucs_ui(installed=True)

    def _on_demucs_error(self, error: str) -> None:
        """Handle demucs download failure."""
        import logging

        logging.getLogger("maestro").error("Demucs model download failed: %s", error)
        self._demucs_btn.setEnabled(True)
        self._demucs_btn.setText("Download")
        self._demucs_status.setText("Download failed")
        self._demucs_status.setProperty("state", "error")
        self._demucs_status.style().unpolish(self._demucs_status)
        self._demucs_status.style().polish(self._demucs_status)
        self.set_error(error)

    def _update_demucs_ui(self, installed: bool) -> None:
        """Update demucs button and status label after install/remove."""
        self._demucs_btn.setEnabled(True)
        if installed:
            self._demucs_btn.setText("Remove")
            self._demucs_btn.setProperty("class", "ghost")
            self._demucs_status.setText("Piano model installed")
            self._demucs_status.setProperty("state", "finished")
        else:
            self._demucs_btn.setText("Download")
            self._demucs_btn.setProperty("class", "ghost")
            self._demucs_status.setText("Piano model not installed")
            self._demucs_status.setProperty("state", "")
        self._demucs_btn.style().unpolish(self._demucs_btn)
        self._demucs_btn.style().polish(self._demucs_btn)
        self._demucs_status.style().unpolish(self._demucs_status)
        self._demucs_status.style().polish(self._demucs_status)
        # Update import panel checkbox
        self._import_panel.set_demucs_available(installed)

    # --- Menu actions ---

    def _on_open_log_click(self) -> None:
        """Handle Open Log menu item click."""
        open_log_file()

    def _show_about(self) -> None:
        """Show the About dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    def _show_disclaimer(self) -> None:
        """Show the Disclaimer dialog."""
        dialog = DisclaimerDialog(self)
        dialog.exec()

    # --- Window events ---

    def closeEvent(self, event) -> None:  # noqa: N802
        """Handle window close."""
        self.signals.exit_requested.emit()
        event.accept()

    # --- Properties for backend state tracking ---

    @property
    def _current_position(self) -> float:
        """Get current playback position from progress bar."""
        bar = self._now_playing._progress_bar
        if bar.maximum() > 0:
            return bar.value() / bar.maximum()
        return 0.0
