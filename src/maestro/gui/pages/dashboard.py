"""Dashboard page — main view after launch.

Two-column layout: fixed 400px scrollable left column with game settings
and transport cards; flexible right column with search bar and song list.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from maestro.game_mode import GameMode
from maestro.gui.controls_panel import ControlsPanel
from maestro.gui.piano_roll import PianoRollWidget
from maestro.gui.progress_panel import NowPlayingPanel
from maestro.gui.song_list import SongListWidget
from maestro.gui.theme import SPACING
from maestro.gui.toggle_switch import ToggleSwitch
from maestro.key_layout import KeyLayout, WwmLayout

# Layouts that disable transpose and sharp handling
_FIXED_LAYOUTS = {KeyLayout.DRUMS, KeyLayout.XYLOPHONE}

# Heartopia layouts that show the sharp handling row
_SHARP_LAYOUTS = {KeyLayout.KEYS_15_DOUBLE, KeyLayout.KEYS_15_TRIPLE}

# WWM layouts that show the sharp handling row
_WWM_SHARP_LAYOUTS = {WwmLayout.KEYS_21}


class DashboardPage(QWidget):
    """Main dashboard with two-column layout.

    Left column (400px, scrollable):
      - Game Settings card (game mode, key layout, sharp, transpose, preview)
      - Transport card (error, now playing, controls, status, speed, piano roll)

    Right column (flexible):
      - Header row (search + refresh)
      - Song list
    """

    def __init__(self, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._config = config

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(SPACING["xl"])

        # ── Left Column (scrollable, fixed 400px) ──────────────────────
        self._left_scroll = QScrollArea()
        self._left_scroll.setWidgetResizable(True)
        self._left_scroll.setFixedWidth(400)
        self._left_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(
            SPACING["md"], SPACING["md"], SPACING["md"], SPACING["md"]
        )
        sidebar_layout.setSpacing(SPACING["md"])

        self._build_game_settings_card(sidebar_layout)
        self._build_transport_card(sidebar_layout)

        sidebar_layout.addStretch()
        self._left_scroll.setWidget(sidebar)

        root.addWidget(self._left_scroll)

        # ── Right Column (flexible) ────────────────────────────────────
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, SPACING["md"], SPACING["md"], SPACING["md"])
        right_layout.setSpacing(SPACING["sm"])

        # Header row: search + refresh
        header_row = QHBoxLayout()
        header_row.setSpacing(SPACING["sm"])

        self._search_entry = QLineEdit()
        self._search_entry.setPlaceholderText("Filter songs...")
        header_row.addWidget(self._search_entry, stretch=1)

        self._refresh_btn = QPushButton("\u21bb Refresh")
        self._refresh_btn.setToolTip("Refresh song list")
        header_row.addWidget(self._refresh_btn)

        right_layout.addLayout(header_row)

        # Song list
        self._song_list = SongListWidget()
        right_layout.addWidget(self._song_list, stretch=1)

        root.addWidget(right, stretch=1)

        # Apply initial visibility rules
        self._update_layout_visibility()
        self._update_options_state()

    # ── Card builders ──────────────────────────────────────────────────

    def _build_game_settings_card(self, parent_layout: QVBoxLayout) -> None:
        """Build the Game Settings card."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])

        # Game mode row
        game_row = QHBoxLayout()
        game_row.setSpacing(SPACING["sm"])
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

        # Key layout row (hidden for WWM)
        self._layout_row = QWidget()
        layout_row_inner = QHBoxLayout(self._layout_row)
        layout_row_inner.setContentsMargins(0, 0, 0, 0)
        layout_row_inner.setSpacing(SPACING["sm"])
        keys_lbl = QLabel("Keys")
        keys_lbl.setProperty("class", "section-heading")
        layout_row_inner.addWidget(keys_lbl)
        layout_row_inner.addStretch()
        self._layout_combo = QComboBox()
        self._layout_combo.addItems([kl.value for kl in KeyLayout])
        layout_str = self._config.get("key_layout", KeyLayout.KEYS_22.value)
        self._layout_combo.setCurrentText(layout_str)
        self._layout_combo.currentTextChanged.connect(self._on_layout_change)
        layout_row_inner.addWidget(self._layout_combo)
        layout.addWidget(self._layout_row)

        # Sharp handling row (visible only for 15-key layouts)
        self._sharp_row = QWidget()
        sharp_inner = QHBoxLayout(self._sharp_row)
        sharp_inner.setContentsMargins(0, 0, 0, 0)
        sharp_inner.setSpacing(SPACING["sm"])
        sharp_lbl = QLabel("Sharps")
        sharp_lbl.setProperty("class", "section-heading")
        sharp_inner.addWidget(sharp_lbl)
        sharp_inner.addStretch()
        self._sharp_combo = QComboBox()
        self._sharp_combo.addItems(["skip", "snap"])
        self._sharp_combo.setCurrentText(self._config.get("sharp_handling", "skip"))
        sharp_inner.addWidget(self._sharp_combo)
        layout.addWidget(self._sharp_row)

        # Transpose toggle row
        transpose_row = QHBoxLayout()
        transpose_row.setSpacing(SPACING["sm"])
        transpose_lbl = QLabel("Transpose to range")
        transpose_lbl.setProperty("class", "caption")
        transpose_row.addWidget(transpose_lbl)
        transpose_row.addStretch()
        self._transpose_toggle = ToggleSwitch(checked=self._config.get("transpose", False))
        transpose_row.addWidget(self._transpose_toggle)
        layout.addLayout(transpose_row)

        # Note preview toggle row
        preview_row = QHBoxLayout()
        preview_row.setSpacing(SPACING["sm"])
        preview_lbl = QLabel("Note preview")
        preview_lbl.setProperty("class", "caption")
        preview_row.addWidget(preview_lbl)
        preview_row.addStretch()
        self._preview_toggle = ToggleSwitch(checked=self._config.get("show_preview", False))
        preview_row.addWidget(self._preview_toggle)
        layout.addLayout(preview_row)

        parent_layout.addWidget(card)

    def _build_transport_card(self, parent_layout: QVBoxLayout) -> None:
        """Build the Transport card — focal point of the sidebar."""
        card = QWidget()
        card.setProperty("class", "surface-card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"])
        layout.setSpacing(SPACING["sm"])

        # Error label (hidden by default)
        self._error_label = QLabel()
        self._error_label.setProperty("state", "error")
        self._error_label.setWordWrap(True)
        self._error_label.setMinimumWidth(1)
        self._error_label.setVisible(False)
        layout.addWidget(self._error_label)

        # Now Playing panel
        self._now_playing = NowPlayingPanel()
        layout.addWidget(self._now_playing)

        # Control buttons
        self._controls = ControlsPanel()
        layout.addWidget(self._controls)

        # Status row
        status_row = QHBoxLayout()
        status_row.setSpacing(SPACING["xs"])
        self._status_label = QLabel("Stopped")
        self._status_label.setProperty("class", "caption")
        status_row.addWidget(self._status_label)
        status_row.addStretch()
        self._key_label = QLabel("")
        self._key_label.setProperty("class", "caption")
        status_row.addWidget(self._key_label)
        layout.addLayout(status_row)

        # Speed row
        speed_row = QHBoxLayout()
        speed_row.setSpacing(SPACING["sm"])
        speed_lbl = QLabel("Speed")
        speed_lbl.setProperty("class", "section-heading")
        speed_row.addWidget(speed_lbl)
        self._speed_slider = QSlider(Qt.Orientation.Horizontal)
        self._speed_slider.setRange(5, 20)
        speed_val = self._config.get("speed", 1.0)
        self._speed_slider.setValue(int(speed_val * 10))
        self._speed_slider.valueChanged.connect(self._on_speed_change)
        speed_row.addWidget(self._speed_slider, stretch=1)
        self._speed_label = QLabel(f"{speed_val:.1f}x")
        self._speed_label.setFixedWidth(48)
        speed_row.addWidget(self._speed_label)
        layout.addLayout(speed_row)

        # Note preview container (visible based on config)
        self._preview_container = QWidget()
        preview_layout = QVBoxLayout(self._preview_container)
        preview_layout.setContentsMargins(0, SPACING["xs"], 0, 0)
        preview_layout.setSpacing(SPACING["xs"])

        # Lookahead selector
        lookahead_row = QHBoxLayout()
        lookahead_row.setSpacing(SPACING["xs"])
        lookahead_lbl = QLabel("Lookahead")
        lookahead_lbl.setProperty("class", "caption")
        lookahead_row.addWidget(lookahead_lbl)
        self._lookahead_combo = QComboBox()
        self._lookahead_combo.addItems(["2", "5", "10"])
        lookahead_val = self._config.get("preview_lookahead", 5)
        self._lookahead_combo.setCurrentText(str(lookahead_val))
        lookahead_row.addWidget(self._lookahead_combo)
        sec_lbl = QLabel("sec")
        sec_lbl.setProperty("class", "caption")
        lookahead_row.addWidget(sec_lbl)
        lookahead_row.addStretch()
        preview_layout.addLayout(lookahead_row)

        # Piano roll canvas
        self._piano_roll = PianoRollWidget()
        preview_layout.addWidget(self._piano_roll)

        layout.addWidget(self._preview_container)
        self._preview_container.setVisible(self._config.get("show_preview", False))

        parent_layout.addWidget(card)

    # ── Visibility helpers ─────────────────────────────────────────────

    def _is_wwm(self) -> bool:
        """Return True if WWM game mode is currently selected."""
        return self._game_combo.currentText() == GameMode.WHERE_WINDS_MEET.value

    def _is_once_human(self) -> bool:
        """Return True if Once Human game mode is currently selected."""
        return self._game_combo.currentText() == GameMode.ONCE_HUMAN.value

    def _update_layout_visibility(self) -> None:
        """Repopulate the key layout dropdown based on game mode."""
        if self._is_once_human():
            # Once Human has a single fixed layout — hide the dropdown
            self._layout_row.setVisible(False)
            return

        self._layout_row.setVisible(True)
        self._layout_combo.blockSignals(True)
        self._layout_combo.clear()
        if self._is_wwm():
            self._layout_combo.addItems([wl.value for wl in WwmLayout])
            wwm_str = self._config.get("wwm_key_layout", WwmLayout.KEYS_36.value)
            self._layout_combo.setCurrentText(wwm_str)
        else:
            self._layout_combo.addItems([kl.value for kl in KeyLayout])
            layout_str = self._config.get("key_layout", KeyLayout.KEYS_22.value)
            self._layout_combo.setCurrentText(layout_str)
        self._layout_combo.blockSignals(False)

    def _update_options_state(self) -> None:
        """Update sharp/transpose visibility based on selected layout."""
        if self._is_once_human():
            # Once Human: all notes playable, no sharp handling needed
            self._sharp_row.setVisible(False)
            self._transpose_toggle.setEnabled(True)
            return

        combo_text = self._layout_combo.currentText()

        if self._is_wwm():
            # WWM mode
            current_wwm = WwmLayout.KEYS_36
            for wl in WwmLayout:
                if wl.value == combo_text:
                    current_wwm = wl
                    break
            self._sharp_row.setVisible(current_wwm in _WWM_SHARP_LAYOUTS)
            self._transpose_toggle.setEnabled(True)
        else:
            # Heartopia mode
            current_layout = KeyLayout.KEYS_22
            for kl in KeyLayout:
                if kl.value == combo_text:
                    current_layout = kl
                    break
            self._sharp_row.setVisible(current_layout in _SHARP_LAYOUTS)
            is_fixed = current_layout in _FIXED_LAYOUTS
            self._transpose_toggle.setEnabled(not is_fixed)

    # ── Public helpers ─────────────────────────────────────────────────

    # ── Slot helpers (internal wiring) ─────────────────────────────────

    def _on_game_mode_change(self, _text: str) -> None:
        """React to game mode change — update layout visibility."""
        self._update_layout_visibility()
        self._update_options_state()

    def _on_layout_change(self, _text: str) -> None:
        """React to key layout change — update options state."""
        self._update_options_state()

    def _on_speed_change(self, value: int) -> None:
        """Update the speed label from slider integer value."""
        speed = value / 10.0
        self._speed_label.setText(f"{speed:.1f}x")
