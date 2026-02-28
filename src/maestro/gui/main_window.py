"""Main application window composing all GUI widgets."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from maestro.game_mode import GameMode
from maestro.gui.about_dialog import AboutDialog, DisclaimerDialog
from maestro.gui.constants import APP_VERSION, GITHUB_REPO
from maestro.gui.controls_panel import ControlsPanel
from maestro.gui.import_panel import ImportPanel
from maestro.gui.piano_roll import PianoRollWidget
from maestro.gui.progress_panel import NowPlayingPanel
from maestro.gui.settings_dialog import SettingsDialog
from maestro.gui.signals import MaestroSignals
from maestro.gui.song_list import SongListWidget
from maestro.gui.update_banner import UpdateBanner
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
        file_menu.addAction("Settings...", self._show_settings)
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

        # ── Left Column: Sidebar (fixed 300px) ───────────────────────

        sidebar = QWidget()
        sidebar.setFixedWidth(300)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 16, 16, 16)
        sidebar_layout.setSpacing(16)

        # -- Settings Card --
        settings_card = QWidget()
        settings_card.setProperty("class", "surface-card")
        settings_card_layout = QVBoxLayout(settings_card)
        settings_card_layout.setContentsMargins(16, 16, 16, 16)
        settings_card_layout.setSpacing(8)

        # Folder selection row
        folder_label = QLabel("FOLDER")
        folder_label.setProperty("class", "overline")
        settings_card_layout.addWidget(folder_label)
        folder_row = QHBoxLayout()
        self._folder_label = QLabel(str(self.songs_folder))
        self._folder_label.setProperty("class", "caption")
        folder_row.addWidget(self._folder_label, stretch=1)
        browse_btn = self._make_button("Browse...", self._on_browse_click)
        folder_row.addWidget(browse_btn)
        settings_card_layout.addLayout(folder_row)

        # Game mode row
        game_label = QLabel("GAME")
        game_label.setProperty("class", "overline")
        settings_card_layout.addWidget(game_label)
        game_row = QHBoxLayout()
        self._game_combo = QComboBox()
        self._game_combo.addItems([mode.value for mode in GameMode])
        game_mode_str = self._config.get("game_mode", GameMode.HEARTOPIA.value)
        self._game_combo.setCurrentText(game_mode_str)
        self._game_combo.currentTextChanged.connect(self._on_game_mode_change)
        game_row.addWidget(self._game_combo)
        game_row.addStretch()
        settings_card_layout.addLayout(game_row)

        # Key layout row (Heartopia only)
        self._layout_row = QWidget()
        layout_row_inner = QVBoxLayout(self._layout_row)
        layout_row_inner.setContentsMargins(0, 0, 0, 0)
        layout_row_inner.setSpacing(8)
        keys_label = QLabel("KEYS")
        keys_label.setProperty("class", "overline")
        layout_row_inner.addWidget(keys_label)
        layout_combo_row = QHBoxLayout()
        self._layout_combo = QComboBox()
        self._layout_combo.addItems([layout.value for layout in KeyLayout])
        self._layout_combo.setCurrentText(self._key_layout.value)
        self._layout_combo.currentTextChanged.connect(self._on_layout_change)
        layout_combo_row.addWidget(self._layout_combo)
        layout_combo_row.addStretch()
        layout_row_inner.addLayout(layout_combo_row)
        settings_card_layout.addWidget(self._layout_row)
        self._update_layout_visibility()

        # Speed control row
        speed_label = QLabel("SPEED")
        speed_label.setProperty("class", "overline")
        settings_card_layout.addWidget(speed_label)
        speed_row = QHBoxLayout()
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(25, 150)
        speed_val = self._config.get("speed", 1.0)
        self._speed_slider.setValue(int(speed_val * 100))
        self._speed_slider.valueChanged.connect(self._on_speed_change)
        speed_row.addWidget(self._speed_slider, stretch=1)
        self._speed_label = QLabel(f"{speed_val:.2f}x")
        self._speed_label.setFixedWidth(45)
        speed_row.addWidget(self._speed_label)
        settings_card_layout.addLayout(speed_row)

        sidebar_layout.addWidget(settings_card)

        # -- Transport Card --
        transport_card = QWidget()
        transport_card.setProperty("class", "surface-card")
        transport_card_layout = QVBoxLayout(transport_card)
        transport_card_layout.setContentsMargins(16, 16, 16, 16)
        transport_card_layout.setSpacing(8)

        # Error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setProperty("state", "error")
        self._error_label.setWordWrap(True)
        self._error_label.setVisible(False)
        transport_card_layout.addWidget(self._error_label)

        # Now Playing panel
        self._now_playing = NowPlayingPanel()
        transport_card_layout.addWidget(self._now_playing)

        # Control buttons
        self._controls = ControlsPanel()
        transport_card_layout.addWidget(self._controls)

        # Status and Key display
        status_row = QHBoxLayout()
        self._status_label = QLabel("Status: Stopped")
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        self._key_label = QLabel("Key: -")
        status_row.addWidget(self._key_label)
        transport_card_layout.addLayout(status_row)

        # Note Preview panel (conditionally shown)
        self._preview_container = QWidget()
        preview_layout = QVBoxLayout(self._preview_container)
        preview_layout.setContentsMargins(0, 0, 0, 0)

        # Lookahead selector
        lookahead_row = QHBoxLayout()
        lookahead_row.addWidget(QLabel("Lookahead:"))
        self._lookahead_combo = QComboBox()
        self._lookahead_combo.addItems(["2", "5", "10"])
        self._lookahead_combo.setCurrentText(str(self._lookahead))
        self._lookahead_combo.currentTextChanged.connect(self._on_lookahead_change)
        lookahead_row.addWidget(self._lookahead_combo)
        lookahead_row.addWidget(QLabel("seconds"))
        lookahead_row.addStretch()
        preview_layout.addLayout(lookahead_row)

        # Piano roll canvas
        self._piano_roll = PianoRollWidget()
        preview_layout.addWidget(self._piano_roll)

        transport_card_layout.addWidget(self._preview_container)
        self._preview_container.setVisible(self._show_preview)

        sidebar_layout.addWidget(transport_card)
        sidebar_layout.addStretch()

        columns.addWidget(sidebar)

        # ── Right Column: Main Area ───────────────────────────────────

        main_area = QWidget()
        main_area_layout = QVBoxLayout(main_area)
        main_area_layout.setContentsMargins(24, 16, 16, 16)
        main_area_layout.setSpacing(12)

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

        # Song detail label
        self._song_detail_label = QLabel("Select a song to see details")
        self._song_detail_label.setProperty("class", "caption")
        self._song_detail_label.setWordWrap(True)
        main_area_layout.addWidget(self._song_detail_label)

        columns.addWidget(main_area, stretch=1)

        root_layout.addLayout(columns, stretch=1)

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

    def _make_button(self, text: str, callback) -> QWidget:
        """Create a styled button."""
        from PySide6.QtWidgets import QPushButton

        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn

    # --- State update handlers ---

    def _on_state_updated(self, state: str) -> None:
        """Handle playback state update from backend."""
        self._status_label.setText(f"Status: {state}")
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
        self._key_label.setText(f"Key: {key or '-'}")

    def _on_upcoming_notes_updated(self, notes: list) -> None:
        """Handle upcoming notes update from backend."""
        self._piano_roll.set_notes(notes, self._current_position, float(self._lookahead))

    def _on_note_compatibility_result(self, playable: int, total: int) -> None:
        """Handle note compatibility result."""
        self._pending_compatibility = (playable, total)
        self._update_song_detail_with_compatibility()

    def _on_error(self, message: str) -> None:
        """Display an error message."""
        self._last_error = message
        self._update_error_label()

    def _on_countdown_tick(self, count: int) -> None:
        """Handle countdown tick from backend."""
        if count > 0:
            self._status_label.setText(f"Status: Starting in {count}...")
        else:
            self._status_label.setText("Status: Playing")

    def _on_favorites_loaded(self, favorites: list) -> None:
        """Handle favorites list loaded from backend."""
        self._favorites = favorites
        self._apply_search_filter()

    # --- Song finish handling ---

    def _on_song_finished(self) -> None:
        """Handle song playback completion."""
        self._status_label.setText("Status: Finished")
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
        """Handle song selection to show details."""
        if song is None:
            return

        info = self._song_info.get(str(song))
        status = self._validation_results.get(str(song), "pending")

        if status == "pending":
            self._song_detail_label.setText("Validating...")
            self._song_detail_label.setProperty("class", "caption")
            self._song_detail_label.setProperty("state", "")
        elif status == "invalid":
            self._song_detail_label.setText("Invalid MIDI file")
            self._song_detail_label.setProperty("state", "error")
            self._song_detail_label.setProperty("class", "")
        elif info:
            duration = info["duration"]
            minutes = int(duration // 60)
            secs = int(duration % 60)
            text = f"{minutes}:{secs:02d} | {info['bpm']} BPM | {info['note_count']} notes"
            self._song_detail_label.setText(text)
            self._song_detail_label.setProperty("state", "")
            self._song_detail_label.setProperty("class", "caption")

            # Request note compatibility from backend
            self.signals.note_compatibility_requested.emit(song)

        self._song_detail_label.style().unpolish(self._song_detail_label)
        self._song_detail_label.style().polish(self._song_detail_label)

        self._update_favorite_button()

    def _update_song_detail_with_compatibility(self) -> None:
        """Append compatibility info to the song detail label."""
        if not hasattr(self, "_pending_compatibility"):
            return

        playable, total = self._pending_compatibility
        if total > 0:
            pct = round(playable / total * 100)
            current_text = self._song_detail_label.text()
            if self._key_layout == KeyLayout.DRUMS:
                compat_text = f" | {pct}% playable on Conga/Cajon (8-key) ({playable}/{total})"
            else:
                compat_text = f" | {pct}% playable ({playable}/{total})"
            if pct < 100:
                compat_text += f" - {total - playable} out of range"
            self._song_detail_label.setText(current_text + compat_text)

        del self._pending_compatibility

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
        self.signals.import_requested.emit(url)

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

    def _on_layout_change(self, selected: str) -> None:
        """Handle key layout dropdown change."""
        for layout in KeyLayout:
            if layout.value == selected:
                self._key_layout = layout
                break
        self.signals.layout_changed.emit(selected)
        # Refresh song detail to show updated compatibility
        self._on_song_select(self._song_list.get_selected_song())

    def _update_layout_visibility(self) -> None:
        """Show layout dropdown only for Heartopia."""
        is_heartopia = self._game_combo.currentText() == GameMode.HEARTOPIA.value
        self._layout_row.setVisible(is_heartopia)

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
            validation_cache=self._validation_cache,
            song_info=self._song_info,
            song_notes=self._song_notes,
        )
        self._validation_worker.song_validated.connect(self._on_song_validated)
        self._validation_worker.validation_finished.connect(self._on_validation_finished)
        self._validation_worker.start()

    def _on_song_validated(self, path_str: str, status: str, info: dict, notes: list) -> None:
        """Handle validation result for a single song."""
        self._validation_results[path_str] = status
        self._song_info[path_str] = info
        self._song_notes[path_str] = notes
        self._song_list.on_song_validated(path_str, status, info, notes)

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

    # --- Menu actions ---

    def _on_open_log_click(self) -> None:
        """Handle Open Log menu item click."""
        open_log_file()

    def _show_settings(self) -> None:
        """Show the Settings dialog."""
        dialog = SettingsDialog(
            parent=self,
            transpose=self._transpose,
            show_preview=self._show_preview,
            sharp_handling=self._sharp_handling,
            key_layout=self._key_layout,
            play_key=self._play_key,
            stop_key=self._stop_key,
            emergency_key=self._emergency_key,
        )

        # Connect settings signals
        dialog.transpose_changed.connect(self._on_transpose_toggle)
        dialog.show_preview_changed.connect(self._on_show_preview_toggle)
        dialog.sharp_handling_changed.connect(self._on_sharp_handling_toggle)
        dialog.hotkey_changed.connect(self._on_hotkey_change)

        dialog.exec()

    def _on_transpose_toggle(self, value: bool) -> None:
        """Handle transpose checkbox toggle."""
        self._transpose = value
        self.signals.transpose_changed.emit(value)

    def _on_show_preview_toggle(self, value: bool) -> None:
        """Handle show preview checkbox toggle."""
        self._show_preview = value
        self._preview_container.setVisible(value)
        self.signals.show_preview_changed.emit(value)

    def _on_sharp_handling_toggle(self, value: str) -> None:
        """Handle sharp handling dropdown change."""
        self._sharp_handling = value
        self.signals.sharp_handling_changed.emit(value)

    def _on_hotkey_change(self, config_key: str, key_name: str) -> None:
        """Handle hotkey change from settings dialog."""
        if config_key == "play_key":
            self._play_key = key_name
        elif config_key == "stop_key":
            self._stop_key = key_name
        elif config_key == "emergency_stop_key":
            self._emergency_key = key_name
        self.signals.hotkey_changed.emit(config_key, key_name)

    def _show_about(self) -> None:
        """Show the About dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    def _show_disclaimer(self) -> None:
        """Show the Disclaimer dialog."""
        dialog = DisclaimerDialog(self)
        dialog.exec()

    # --- Window events ---

    def closeEvent(self, event) -> None:
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
