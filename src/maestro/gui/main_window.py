"""Main application window — thin shell around IconRail + QStackedWidget pages."""

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QStackedWidget,
    QWidget,
)

from maestro.game_mode import GameMode
from maestro.gui.constants import APP_VERSION, GITHUB_REPO
from maestro.gui.exit_dialog import ExitDialog
from maestro.gui.icon_rail import (
    PAGE_DASHBOARD,
    PAGE_INFO,
    PAGE_LOG,
    PAGE_SETTINGS,
    IconRail,
)
from maestro.gui.pages.dashboard import DashboardPage
from maestro.gui.pages.info_page import InfoPage
from maestro.gui.pages.log_page import LogPage
from maestro.gui.pages.settings_page import SettingsPage
from maestro.gui.signals import MaestroSignals
from maestro.gui.theme import apply_theme
from maestro.gui.workers import UpdateCheckWorker, ValidationWorker
from maestro.key_layout import KeyLayout, WwmLayout
from maestro.update_checker import check_for_updates

_PAGE_TITLES = ["Dashboard", "Settings", "About", "Error Log"]


class MainWindow(QMainWindow):
    """Main application window for Maestro — icon rail + paged layout."""

    def __init__(
        self,
        songs_folder: Path,
        config: dict,
    ) -> None:
        super().__init__()

        self.signals = MaestroSignals()

        self.songs_folder = songs_folder
        self._config = config

        # Resolve key layout enums
        self._key_layout = KeyLayout.KEYS_22
        layout_str = config.get("key_layout", "22-key (Full)")
        for layout in KeyLayout:
            if layout.value == layout_str:
                self._key_layout = layout
                break

        self._wwm_layout = WwmLayout.KEYS_36
        wwm_str = config.get("wwm_key_layout", "36-key (Full)")
        for wl in WwmLayout:
            if wl.value == wwm_str:
                self._wwm_layout = wl
                break

        self._sharp_handling = config.get("sharp_handling", "skip")
        self._transpose = config.get("transpose", False)
        self._lookahead = config.get("preview_lookahead", 5)
        self._show_preview = config.get("show_preview", False)
        self._auto_minimize_on_play = config.get("auto_minimize_on_play", True)

        # State
        self._validation_results: dict[str, str] = {}
        self._song_info: dict[str, dict] = {}
        self._song_notes: dict[str, list] = {}
        self._validation_cache: dict[str, tuple[float, bool]] = {}
        self._last_error: str = ""
        self._prev_state: str = "Stopped"
        self._flash_count: int = 0
        self._original_title: str = "Maestro - Dashboard"
        self._auto_minimized: bool = False
        self._validation_worker: ValidationWorker | None = None
        self._update_worker: UpdateCheckWorker | None = None

        self._setup_window(config)
        self._create_ui(config)
        self._connect_internal_signals()

        # First-launch check
        if not config.get("disclaimer_accepted", False):
            self._enter_first_launch_mode()
        else:
            self._rail.set_active(PAGE_DASHBOARD)

        # Load songs and start validation
        self._refresh_songs()

        # Check for updates in background
        if config.get("check_updates_on_launch", True):
            self._background_update_check()

    # ── Window Setup ──────────────────────────────────────────────────

    def _setup_window(self, config: dict) -> None:
        """Configure the main window properties."""
        self.setWindowTitle(self._original_title)
        self.setMinimumSize(900, 600)

        # Window title bar icon — app-wide icon is set earlier in main.py
        # (before splash screen) so the taskbar icon is correct from the start.
        app = QApplication.instance()
        if isinstance(app, QApplication) and not app.windowIcon().isNull():
            self.setWindowIcon(app.windowIcon())

        # Size to 80% of screen or fullscreen
        if config.get("start_fullscreen", False):
            self.showMaximized()
        else:
            primary = QApplication.primaryScreen()
            if primary is None:
                self.resize(900, 600)
                return
            screen = primary.availableGeometry()
            width = int(screen.width() * 0.8)
            height = int(screen.height() * 0.8)
            self.resize(width, height)
            self.move(
                screen.x() + (screen.width() - width) // 2,
                screen.y() + (screen.height() - height) // 2,
            )

    # ── UI Construction ───────────────────────────────────────────────

    def _create_ui(self, config: dict) -> None:
        """Build the icon rail + page stack layout."""
        central = QWidget()
        root = QHBoxLayout(central)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Icon rail
        self._rail = IconRail()
        root.addWidget(self._rail)

        # Page stack
        self._stack = QStackedWidget()

        self._dashboard = DashboardPage(config)
        self._settings = SettingsPage(config)
        self._info = InfoPage(first_launch=not config.get("disclaimer_accepted", False))
        self._log = LogPage()

        self._stack.addWidget(self._dashboard)  # index 0
        self._stack.addWidget(self._settings)  # index 1
        self._stack.addWidget(self._info)  # index 2
        self._stack.addWidget(self._log)  # index 3

        root.addWidget(self._stack, stretch=1)
        self.setCentralWidget(central)

        # Set up settings page with initial state
        self._settings.set_folder(str(self.songs_folder), 0)

    # ── Signal Connections ────────────────────────────────────────────

    def _connect_internal_signals(self) -> None:
        """Wire page signals to MaestroSignals and internal handlers."""
        d = self._dashboard
        s = self._settings

        # --- Icon rail ---
        self._rail.page_changed.connect(self._on_page_changed)
        self._rail.exit_clicked.connect(self._on_exit_click)

        # --- Dashboard → MaestroSignals ---
        d._controls.play_clicked.connect(self._on_play_click)
        d._controls.stop_clicked.connect(self._on_stop_click)
        d._controls.favorite_clicked.connect(self._on_favorite_click)
        d._refresh_btn.clicked.connect(self._refresh_songs)
        d._song_list.song_selected.connect(self._on_song_select)
        d._song_list.song_double_clicked.connect(self._on_double_click)
        d._game_combo.currentTextChanged.connect(self._on_game_mode_change)
        d._layout_combo.currentTextChanged.connect(self._on_layout_change)
        d._speed_slider.valueChanged.connect(self._on_speed_change)
        d._search_entry.textChanged.connect(self._on_search_change)
        d._lookahead_combo.currentTextChanged.connect(self._on_lookahead_change)
        d._transpose_toggle.toggled.connect(self._on_transpose_toggle)
        d._preview_toggle.toggled.connect(self._on_show_preview_toggle)
        d._sharp_combo.currentTextChanged.connect(self._on_sharp_handling_change)
        d._import_panel.import_clicked.connect(self._on_import_request)

        # --- Settings page signals ---
        s.theme_changed.connect(self._on_theme_change)
        s.folder_browse_requested.connect(self._on_browse_click)
        s.hotkey_changed.connect(self._on_hotkey_change)
        s.fullscreen_changed.connect(self._on_fullscreen_change)
        s.auto_minimize_changed.connect(self._on_auto_minimize_change)
        s.check_updates_changed.connect(self._on_check_updates_change)
        s.countdown_delay_changed.connect(self.signals.countdown_delay_changed)
        s.check_now_requested.connect(self._manual_update_check)

        # --- Info page signals ---
        self._info.disclaimer_accepted.connect(self._on_disclaimer_accepted)
        self._info.disclaimer_rejected.connect(self._on_disclaimer_rejected)

        # --- Backend → GUI state updates ---
        self.signals.state_updated.connect(self._on_state_updated)
        self.signals.position_updated.connect(self._on_position_updated)
        self.signals.current_song_updated.connect(d._now_playing.update_song)
        self.signals.last_key_updated.connect(self._on_last_key_updated)
        self.signals.upcoming_notes_updated.connect(self._on_upcoming_notes_updated)
        self.signals.note_compatibility_result.connect(self._on_note_compatibility_result)
        self.signals.error_occurred.connect(self._on_error)
        self.signals.song_finished.connect(self._on_song_finished)
        self.signals.countdown_tick.connect(self._on_countdown_tick)
        self.signals.favorites_loaded.connect(self._on_favorites_loaded)

        # Import signals
        self.signals.import_progress.connect(d._import_panel.show_progress)
        self.signals.import_percent.connect(d._import_panel.set_percent)
        self.signals.import_finished.connect(self._on_import_finished)
        self.signals.import_error.connect(d._import_panel.show_error)

    # ── Page Navigation ───────────────────────────────────────────────

    def _on_page_changed(self, index: int) -> None:
        """Switch page stack and update window title."""
        self._stack.setCurrentIndex(index)
        if 0 <= index < len(_PAGE_TITLES):
            title = f"Maestro - {_PAGE_TITLES[index]}"
            self._original_title = title
            self.setWindowTitle(title)

    def _on_exit_click(self) -> None:
        """Handle exit icon click — show confirmation dialog."""
        dialog = ExitDialog(self)
        if dialog.exec():
            self.signals.exit_requested.emit()

    # ── First-Launch Disclaimer Flow ──────────────────────────────────

    def _enter_first_launch_mode(self) -> None:
        """Disable all pages except Info until disclaimer is accepted."""
        self._rail.set_disabled_pages({PAGE_DASHBOARD, PAGE_SETTINGS, PAGE_LOG})
        self._rail.set_active(PAGE_INFO)
        self._stack.setCurrentIndex(PAGE_INFO)
        self.setWindowTitle("Maestro - Welcome")

    def _on_disclaimer_accepted(self) -> None:
        """Handle disclaimer acceptance — unlock all pages."""
        self._rail.set_disabled_pages(set())
        self._rail.set_active(PAGE_DASHBOARD)
        self._stack.setCurrentIndex(PAGE_DASHBOARD)
        self.setWindowTitle("Maestro - Dashboard")

    def _on_disclaimer_rejected(self) -> None:
        """Handle disclaimer rejection — close app."""
        QApplication.quit()

    # ── State Update Handlers ─────────────────────────────────────────

    def _on_state_updated(self, state: str) -> None:
        """Handle playback state update from backend."""
        d = self._dashboard
        d._status_label.setText(state)
        if state == "Finished":
            d._status_label.setProperty("state", "finished")
        else:
            d._status_label.setProperty("state", "")
        d._status_label.style().unpolish(d._status_label)
        d._status_label.style().polish(d._status_label)

        # Detect song finish
        if self._prev_state == "Playing" and state == "Stopped":
            self._on_song_finished()
        self._prev_state = state

    def _on_position_updated(self, position: float, duration: float) -> None:
        """Handle position update from backend."""
        self._dashboard._now_playing.update_progress(position, duration)

    def _on_last_key_updated(self, key: str) -> None:
        """Handle last key update from backend."""
        self._dashboard._key_label.setText(key.upper() if key else "")

    def _on_upcoming_notes_updated(self, notes: list) -> None:
        """Handle upcoming notes update from backend."""
        self._dashboard._piano_roll.set_notes(notes, self._current_position, float(self._lookahead))

    def _on_note_compatibility_result(self, playable: int, total: int) -> None:
        """Handle note compatibility result — update the song item."""
        song = self._dashboard._song_list.get_selected_song()
        if song:
            self._dashboard._song_list.update_song_compatibility(str(song), playable, total)

    def _on_error(self, message: str) -> None:
        """Display an error message on the dashboard."""
        self._last_error = message
        self._update_error_label()

    def _on_countdown_tick(self, count: int) -> None:
        """Handle countdown tick from backend."""
        if count > 0:
            self._dashboard._status_label.setText(f"Starting in {count}...")
        else:
            self._dashboard._status_label.setText("Playing")

    def _on_favorites_loaded(self, favorites: list) -> None:
        """Handle favorites list loaded from backend."""
        self._favorites = favorites
        self._apply_search_filter()

    # ── Song Finish Handling ──────────────────────────────────────────

    def _on_song_finished(self) -> None:
        """Handle song playback completion."""
        d = self._dashboard
        d._status_label.setText("Finished")
        d._status_label.setProperty("state", "finished")
        d._status_label.style().unpolish(d._status_label)
        d._status_label.style().polish(d._status_label)
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

    # ── User Action Handlers ──────────────────────────────────────────

    def _should_auto_minimize(self) -> bool:
        """Check if auto-minimize should be applied."""
        if not self._auto_minimize_on_play:
            return False
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
        song = self._dashboard._song_list.get_selected_song()
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
        song = self._dashboard._song_list.get_selected_song()
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

    def _on_import_request(self, url: str, _isolate: bool) -> None:
        """Handle import button click from ImportPanel."""
        self._dashboard._import_panel.set_importing(True)
        self.signals.import_requested.emit(url, False)

    def _on_import_finished(self, filename: str) -> None:
        """Handle successful import completion."""
        self._dashboard._import_panel.set_importing(False)
        self._dashboard._import_panel.show_success(f"Downloaded: {filename}")
        self._refresh_songs()

    def _update_favorite_button(self) -> None:
        """Update favorite button star based on selected song."""
        song = self._dashboard._song_list.get_selected_song()
        if song is None:
            self._dashboard._controls.set_favorite(False)
            return
        favorites = getattr(self, "_favorites", [])
        self._dashboard._controls.set_favorite(song.stem in favorites)

    def _on_browse_click(self) -> None:
        """Handle browse button click from settings page."""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Songs Folder", str(self.songs_folder)
        )
        if folder:
            self.songs_folder = Path(folder)
            self._validation_cache.clear()
            self._refresh_songs()
            self.signals.folder_changed.emit(self.songs_folder)
            # Update settings page
            songs_count = len(self._dashboard._song_list.get_songs())
            self._settings.set_folder(str(self.songs_folder), songs_count)

    def _on_game_mode_change(self, selected: str) -> None:
        """Handle game mode dropdown change."""
        self.signals.game_mode_changed.emit(selected)
        # Refresh song compatibility
        self._on_song_select(self._dashboard._song_list.get_selected_song())

    def _on_layout_change(self, selected: str) -> None:
        """Handle key layout dropdown change — routes to Heartopia or WWM signal."""
        is_once_human = self._dashboard._game_combo.currentText() == GameMode.ONCE_HUMAN.value
        if is_once_human:
            return  # No layout variants for Once Human
        is_wwm = self._dashboard._game_combo.currentText() == GameMode.WHERE_WINDS_MEET.value
        if is_wwm:
            for wl in WwmLayout:
                if wl.value == selected:
                    self._wwm_layout = wl
                    break
            self.signals.wwm_layout_changed.emit(selected)
        else:
            for layout in KeyLayout:
                if layout.value == selected:
                    self._key_layout = layout
                    break
            self.signals.layout_changed.emit(selected)
        self._on_song_select(self._dashboard._song_list.get_selected_song())

    def _on_speed_change(self, value: int) -> None:
        """Handle speed slider change (value is in tenths)."""
        speed = value / 10.0
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

    def _on_transpose_toggle(self, value: bool) -> None:
        """Handle transpose toggle change — re-validate to update playable notes."""
        self._transpose = value
        self.signals.transpose_changed.emit(value)
        # Re-run validation so playable note counts update in the song list
        self._validation_cache.clear()
        self._start_validation()

    def _on_show_preview_toggle(self, value: bool) -> None:
        """Handle show preview toggle change."""
        self._show_preview = value
        self._dashboard._preview_container.setVisible(value)
        self.signals.show_preview_changed.emit(value)

    def _on_sharp_handling_change(self, value: str) -> None:
        """Handle sharp handling dropdown change."""
        self._sharp_handling = value
        self.signals.sharp_handling_changed.emit(value)

    # ── Settings Page Handlers ────────────────────────────────────────

    def _on_theme_change(self, theme: str) -> None:
        """Handle theme toggle from settings page."""
        dark = theme == "dark"
        app = QApplication.instance()
        if isinstance(app, QApplication):
            apply_theme(app, dark=dark)
        # Force repaint of custom-painted widget (reads COLORS dict)
        self._rail.update()
        self.signals.theme_changed.emit(theme)

    def _on_hotkey_change(self, config_key: str, key_name: str) -> None:
        """Handle hotkey change from settings page."""
        self.signals.hotkey_changed.emit(config_key, key_name)

    def _on_fullscreen_change(self, fullscreen: bool) -> None:
        """Handle fullscreen toggle from settings page."""
        self._config["start_fullscreen"] = fullscreen

    def _on_auto_minimize_change(self, minimize: bool) -> None:
        """Handle auto-minimize toggle from settings page."""
        self._auto_minimize_on_play = minimize
        self._config["auto_minimize_on_play"] = minimize

    def _on_check_updates_change(self, check: bool) -> None:
        """Handle check-updates-on-launch toggle from settings page."""
        self._config["check_updates_on_launch"] = check

    # ── Song Management ───────────────────────────────────────────────

    def _refresh_songs(self) -> None:
        """Refresh the song list from disk."""
        self._dashboard._song_list.load_songs(self.songs_folder)

        for song in self._dashboard._song_list.get_songs():
            self._validation_results[str(song)] = "pending"

        self._apply_search_filter()
        self._start_validation()

        # Update settings page song count
        songs_count = len(self._dashboard._song_list.get_songs())
        self._settings.set_folder(str(self.songs_folder), songs_count)

    def _apply_search_filter(self) -> None:
        """Apply current search filter to song list."""
        search_term = self._dashboard._search_entry.text()
        favorites = getattr(self, "_favorites", [])
        self._dashboard._song_list.apply_filter(search_term, favorites, self._validation_results)

    def _start_validation(self) -> None:
        """Start background MIDI validation."""
        songs = self._dashboard._song_list.get_songs()
        if not songs:
            return

        self._validation_worker = ValidationWorker(
            songs=songs,
            key_layout=self._key_layout,
            game_mode=self._dashboard._game_combo.currentText(),
            transpose=self._transpose,
            sharp_handling=self._sharp_handling,
            validation_cache=self._validation_cache,
            song_info=self._song_info,
            song_notes=self._song_notes,
            wwm_layout=self._wwm_layout,
        )
        self._validation_worker.song_validated.connect(self._on_song_validated)
        self._validation_worker.validation_finished.connect(self._on_validation_finished)
        self._validation_worker.start()

    def _on_song_validated(
        self,
        path_str: str,
        status: str,
        info: dict,
        notes: list,
        playable: int,
        total: int,
    ) -> None:
        """Handle validation result for a single song."""
        self._validation_results[path_str] = status
        self._song_info[path_str] = info
        self._song_notes[path_str] = notes
        self._dashboard._song_list.on_song_validated(path_str, status, info, notes)
        if status == "valid" and total > 0:
            self._dashboard._song_list.update_song_compatibility(path_str, playable, total)

    def _on_validation_finished(self) -> None:
        """Handle validation completion."""
        self._apply_search_filter()

    # ── Update Checking ───────────────────────────────────────────────

    def _background_update_check(self) -> None:
        """Check for updates in a background thread."""
        self._update_worker = UpdateCheckWorker(APP_VERSION, GITHUB_REPO, timeout=5)
        self._update_worker.update_result.connect(self._on_update_check_result)
        self._update_worker.start()

    def _on_update_check_result(self, update_info) -> None:
        """Handle background update check result."""
        if update_info.has_update:
            self._settings.set_update_status(f"Update available: v{update_info.latest_version}")
            self._settings.set_release_url(update_info.release_url)
            # Show badge on settings icon
            self._rail.set_badge(PAGE_SETTINGS, True)

    def _manual_update_check(self) -> None:
        """Manually check for updates (from settings page)."""
        self._settings.set_update_progress_visible(True)
        self._settings._check_now_btn.setEnabled(False)
        self.setCursor(Qt.CursorShape.WaitCursor)

        update_info = check_for_updates(APP_VERSION, GITHUB_REPO, timeout=10)
        self.unsetCursor()
        self._settings.set_update_progress_visible(False)
        self._settings._check_now_btn.setEnabled(True)

        if update_info.error:
            self._settings.set_update_status(f"Error: {update_info.error}")
            self._settings.set_release_url(None)
        elif update_info.has_update:
            self._settings.set_update_status(f"Update available: v{update_info.latest_version}")
            self._settings.set_release_url(update_info.release_url)
            self._rail.set_badge(PAGE_SETTINGS, True)
        else:
            self._settings.set_update_status(f"Up to date (v{APP_VERSION})")
            self._settings.set_release_url(None)

    # ── Error Handling ────────────────────────────────────────────────

    def _update_error_label(self) -> None:
        """Update the dashboard error label visibility and text."""
        d = self._dashboard
        if self._last_error:
            d._error_label.setText(self._last_error)
            d._error_label.setVisible(True)
        else:
            d._error_label.setVisible(False)

    def set_error(self, message: str) -> None:
        """Set error message to display on dashboard."""
        self._last_error = message
        self._update_error_label()

    # ── Window Events ─────────────────────────────────────────────────

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        """Handle window close — show exit confirmation dialog."""
        dialog = ExitDialog(self)
        if dialog.exec():
            self.signals.exit_requested.emit()
            event.accept()
        else:
            event.ignore()

    # ── Properties ────────────────────────────────────────────────────

    @property
    def _current_position(self) -> float:
        """Get current playback position from progress bar."""
        bar = self._dashboard._now_playing._progress_bar
        if bar.maximum() > 0:
            return bar.value() / bar.maximum()
        return 0.0
