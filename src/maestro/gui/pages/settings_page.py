"""Settings page with Library, Appearance, Hotkeys, Demucs, and Updates cards.

A scrollable page containing five surface-card sections for all user-facing
settings.  Each card groups related options with toggle switches, hotkey
binding, and action buttons.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.constants import BINDABLE_KEYS_QT
from maestro.gui.theme import SPACING
from maestro.gui.toggle_switch import ToggleSwitch
from maestro.gui.utils import check_hotkey_conflict

# ---------------------------------------------------------------------------
# Human-readable display names for config key values
# ---------------------------------------------------------------------------

_KEY_DISPLAY: dict[str, str] = {v: v.upper().replace("_", " ") for v in BINDABLE_KEYS_QT.values()}


class SettingsPage(QWidget):
    """Settings page containing Library, Appearance, Hotkeys, Demucs, and Updates cards.

    Parameters
    ----------
    config : dict
        Application configuration dictionary.  Expected keys include
        ``theme``, ``start_fullscreen``, ``auto_minimize_on_play``,
        ``check_updates_on_launch``, ``play_key``, ``stop_key``,
        ``emergency_stop_key``.
    parent : QWidget | None
        Optional parent widget.
    """

    # ------------------------------------------------------------------
    # Signals
    # ------------------------------------------------------------------

    theme_changed = Signal(str)  # "dark" or "light"
    folder_browse_requested = Signal()
    hotkey_changed = Signal(str, str)  # (config_key, new_value)
    fullscreen_changed = Signal(bool)
    auto_minimize_changed = Signal(bool)
    check_updates_changed = Signal(bool)
    demucs_action_requested = Signal()
    check_now_requested = Signal()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(self, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config

        # Hotkey binding state
        self._listening_for: str | None = None
        self._play_key: str = config.get("play_key", "f2")
        self._stop_key: str = config.get("stop_key", "f3")
        self._emergency_key: str = config.get("emergency_stop_key", "escape")

        self._setup_ui()

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        """Build the scrollable page layout with five cards."""
        # Outer layout holds the scroll area
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(scroll.Shape.NoFrame)

        # Inner content widget with max width to prevent horizontal stretching
        content = QWidget()
        content.setMaximumWidth(640)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])
        layout.setSpacing(SPACING["lg"])

        layout.addWidget(self._build_library_card())
        layout.addWidget(self._build_appearance_card())
        layout.addWidget(self._build_hotkeys_card())
        layout.addWidget(self._build_demucs_card())
        layout.addWidget(self._build_updates_card())
        layout.addStretch()

        # Center the content in the scroll area
        scroll_content = QWidget()
        scroll_layout = QHBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.addStretch()
        scroll_layout.addWidget(content)
        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    # Card builders
    # ------------------------------------------------------------------

    def _build_library_card(self) -> QWidget:
        """Build the Library card with folder path and browse button."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        lay.setSpacing(SPACING["sm"])

        heading = QLabel("Library")
        heading.setProperty("class", "section-heading")
        lay.addWidget(heading)

        self._folder_label = QLabel("No folder selected")
        self._folder_label.setProperty("class", "caption")
        self._folder_label.setWordWrap(True)
        lay.addWidget(self._folder_label)

        self._song_count_label = QLabel("")
        self._song_count_label.setProperty("class", "caption")
        lay.addWidget(self._song_count_label)

        self._browse_btn = QPushButton("Browse")
        self._browse_btn.clicked.connect(self.folder_browse_requested.emit)
        lay.addWidget(self._browse_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        return card

    def _build_appearance_card(self) -> QWidget:
        """Build the Appearance card with theme, fullscreen, and minimize toggles."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        lay.setSpacing(SPACING["sm"])

        heading = QLabel("Appearance")
        heading.setProperty("class", "section-heading")
        lay.addWidget(heading)

        # Dark mode toggle
        self._theme_toggle = ToggleSwitch(
            checked=(self._config.get("theme", "dark") == "dark")
        )
        self._theme_toggle.toggled.connect(self._on_theme_toggled)
        lay.addLayout(self._toggle_row("Dark mode", self._theme_toggle))

        # Start fullscreen toggle
        self._fullscreen_toggle = ToggleSwitch(
            checked=bool(self._config.get("start_fullscreen", False))
        )
        self._fullscreen_toggle.toggled.connect(self.fullscreen_changed.emit)
        lay.addLayout(self._toggle_row("Start fullscreen", self._fullscreen_toggle))

        # Auto-minimize on play toggle
        self._minimize_toggle = ToggleSwitch(
            checked=bool(self._config.get("auto_minimize_on_play", True))
        )
        self._minimize_toggle.toggled.connect(self.auto_minimize_changed.emit)
        lay.addLayout(self._toggle_row("Auto-minimize on play", self._minimize_toggle))

        return card

    def _build_hotkeys_card(self) -> QWidget:
        """Build the Hotkeys card with bind rows for play, stop, emergency."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        lay.setSpacing(SPACING["sm"])

        heading = QLabel("Hotkeys")
        heading.setProperty("class", "section-heading")
        lay.addWidget(heading)

        # Play key row
        self._hotkey_play_label = QLabel(self._display_key(self._play_key))
        play_row, self._play_bind_btn = self._hotkey_row(
            "Play", self._hotkey_play_label, "play_key"
        )
        lay.addLayout(play_row)

        # Stop key row
        self._hotkey_stop_label = QLabel(self._display_key(self._stop_key))
        stop_row, self._stop_bind_btn = self._hotkey_row(
            "Stop", self._hotkey_stop_label, "stop_key"
        )
        lay.addLayout(stop_row)

        # Emergency stop key row
        self._hotkey_emergency_label = QLabel(
            self._display_key(self._emergency_key)
        )
        emergency_row, self._emergency_bind_btn = self._hotkey_row(
            "Emergency", self._hotkey_emergency_label, "emergency_stop_key"
        )
        lay.addLayout(emergency_row)

        return card

    def _build_demucs_card(self) -> QWidget:
        """Build the Piano Isolation (Demucs) card."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        lay.setSpacing(SPACING["sm"])

        heading = QLabel("Piano Isolation")
        heading.setProperty("class", "section-heading")
        lay.addWidget(heading)

        desc = QLabel(
            "Download the Demucs model to isolate piano audio from imported "
            "tracks. This improves MIDI transcription accuracy."
        )
        desc.setProperty("class", "caption")
        desc.setWordWrap(True)
        lay.addWidget(desc)

        self._demucs_status = QLabel("Checking...")
        self._demucs_status.setProperty("class", "caption")
        lay.addWidget(self._demucs_status)

        self._demucs_btn = QPushButton("Download")
        self._demucs_btn.clicked.connect(self.demucs_action_requested.emit)
        lay.addWidget(self._demucs_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        return card

    def _build_updates_card(self) -> QWidget:
        """Build the Updates card with toggle, status, and check button."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        lay.setSpacing(SPACING["sm"])

        heading = QLabel("Updates")
        heading.setProperty("class", "section-heading")
        lay.addWidget(heading)

        # Check on launch toggle
        self._update_toggle = ToggleSwitch(
            checked=bool(self._config.get("check_updates_on_launch", True))
        )
        self._update_toggle.toggled.connect(self.check_updates_changed.emit)
        lay.addLayout(self._toggle_row("Check on launch", self._update_toggle))

        self._update_status = QLabel("")
        self._update_status.setProperty("class", "caption")
        lay.addWidget(self._update_status)

        self._update_progress = QProgressBar()
        self._update_progress.setRange(0, 0)
        self._update_progress.hide()
        lay.addWidget(self._update_progress)

        self._check_now_btn = QPushButton("Check Now")
        self._check_now_btn.clicked.connect(self.check_now_requested.emit)
        lay.addWidget(self._check_now_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        return card

    # ------------------------------------------------------------------
    # Layout helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _toggle_row(label_text: str, toggle: ToggleSwitch) -> QHBoxLayout:
        """Create a horizontal row: label on left, toggle on right."""
        row = QHBoxLayout()
        row.setSpacing(SPACING["sm"])
        lbl = QLabel(label_text)
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(toggle)
        return row

    def _hotkey_row(
        self, action_text: str, badge_label: QLabel, config_key: str
    ) -> tuple[QHBoxLayout, QPushButton]:
        """Create a hotkey binding row.

        Returns the layout and the Bind button for external reference.
        """
        row = QHBoxLayout()
        row.setSpacing(SPACING["sm"])

        action_label = QLabel(action_text)
        action_label.setFixedWidth(90)
        row.addWidget(action_label)

        badge_label.setProperty("class", "key-badge")
        badge_label.setMinimumWidth(80)
        badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(badge_label)

        bind_btn = QPushButton("Bind")
        bind_btn.setFixedWidth(72)
        bind_btn.clicked.connect(lambda: self._start_listening(config_key))
        row.addWidget(bind_btn)

        row.addStretch()
        return row, bind_btn

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def set_folder(self, path: str, count: int) -> None:
        """Update the library folder display."""
        self._folder_label.setText(path or "No folder selected")
        self._song_count_label.setText(f"{count} songs" if count else "")

    def set_demucs_status(self, installed: bool) -> None:
        """Update the demucs status and button text."""
        if installed:
            self._demucs_status.setText("Model installed")
            self._demucs_btn.setText("Remove")
        else:
            self._demucs_status.setText("Model not installed")
            self._demucs_btn.setText("Download")

    def set_update_status(self, text: str) -> None:
        """Update the update check status text."""
        self._update_status.setText(text)

    def set_update_progress_visible(self, visible: bool) -> None:
        """Show or hide the indeterminate progress bar."""
        self._update_progress.setVisible(visible)

    # ------------------------------------------------------------------
    # Hotkey binding
    # ------------------------------------------------------------------

    def _start_listening(self, config_key: str) -> None:
        """Enter hotkey-listen mode for the given config key."""
        self._listening_for = config_key
        # Update the badge to indicate listening
        badge = self._badge_for_key(config_key)
        if badge:
            badge.setText("Press a key...")
        self.grabKeyboard()

    def keyPressEvent(self, event: QKeyEvent) -> None:  # noqa: N802
        """Capture a key press during hotkey binding."""
        if self._listening_for is None:
            super().keyPressEvent(event)
            return

        config_key = self._listening_for
        qt_key = event.key()

        # Check if the pressed key is bindable
        if qt_key not in BINDABLE_KEYS_QT:
            self._stop_listening()
            return

        new_value = BINDABLE_KEYS_QT[qt_key]

        # Check for conflicts
        conflict = check_hotkey_conflict(
            new_value,
            config_key,
            self._play_key,
            self._stop_key,
            self._emergency_key,
        )
        if conflict is not None:
            self._stop_listening()
            QMessageBox.warning(
                self,
                "Hotkey Conflict",
                f"'{self._display_key(new_value)}' is already bound to {conflict}.",
            )
            return

        # Apply the new binding
        if config_key == "play_key":
            self._play_key = new_value
        elif config_key == "stop_key":
            self._stop_key = new_value
        elif config_key == "emergency_stop_key":
            self._emergency_key = new_value

        badge = self._badge_for_key(config_key)
        if badge:
            badge.setText(self._display_key(new_value))

        self._stop_listening()
        self.hotkey_changed.emit(config_key, new_value)

    def _stop_listening(self) -> None:
        """Exit hotkey-listen mode and restore the badge if unchanged."""
        config_key = self._listening_for
        self._listening_for = None
        self.releaseKeyboard()

        # Restore badge text if it still says "Press a key..."
        if config_key:
            badge = self._badge_for_key(config_key)
            if badge and badge.text() == "Press a key...":
                current = self._current_key_for(config_key)
                badge.setText(self._display_key(current))

    def _badge_for_key(self, config_key: str) -> QLabel | None:
        """Return the badge label for the given config key."""
        mapping = {
            "play_key": self._hotkey_play_label,
            "stop_key": self._hotkey_stop_label,
            "emergency_stop_key": self._hotkey_emergency_label,
        }
        return mapping.get(config_key)

    def _current_key_for(self, config_key: str) -> str:
        """Return the current key value for the given config key."""
        mapping = {
            "play_key": self._play_key,
            "stop_key": self._stop_key,
            "emergency_stop_key": self._emergency_key,
        }
        return mapping.get(config_key, "")

    # ------------------------------------------------------------------
    # Theme callback
    # ------------------------------------------------------------------

    def _on_theme_toggled(self, checked: bool) -> None:
        """Emit theme_changed with 'dark' or 'light'."""
        self.theme_changed.emit("dark" if checked else "light")

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _display_key(key_value: str) -> str:
        """Return a human-readable display string for a key config value."""
        return _KEY_DISPLAY.get(key_value, key_value.upper())
