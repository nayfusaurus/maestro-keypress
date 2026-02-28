"""Settings dialog with transpose, preview, sharp handling, and hotkey binding."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.constants import BINDABLE_KEYS_QT
from maestro.gui.utils import center_dialog
from maestro.key_layout import KeyLayout


class SettingsDialog(QDialog):
    """Modal settings dialog for transpose, preview, sharp handling, and hotkey remapping."""

    transpose_changed = Signal(bool)
    show_preview_changed = Signal(bool)
    sharp_handling_changed = Signal(str)
    hotkey_changed = Signal(str, str)  # config_key, key_name
    demucs_download_requested = Signal()  # User wants to download demucs

    def __init__(
        self,
        parent: QWidget | None,
        transpose: bool,
        show_preview: bool,
        sharp_handling: str,
        key_layout: KeyLayout,
        play_key: str,
        stop_key: str,
        emergency_key: str,
        demucs_available: bool = False,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(340, 520)
        self.setModal(True)

        self._play_key = play_key
        self._stop_key = stop_key
        self._emergency_key = emergency_key
        self._listening_for: str | None = None  # config_key being bound

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Transpose checkbox
        self._transpose_cb = QCheckBox("Transpose notes to playable range")
        self._transpose_cb.setChecked(transpose)
        self._transpose_cb.stateChanged.connect(
            lambda state: self.transpose_changed.emit(state == Qt.CheckState.Checked.value)
        )
        if key_layout == KeyLayout.DRUMS:
            self._transpose_cb.setEnabled(False)
        layout.addWidget(self._transpose_cb)

        # Show preview checkbox
        self._preview_cb = QCheckBox("Show note preview panel")
        self._preview_cb.setChecked(show_preview)
        self._preview_cb.stateChanged.connect(
            lambda state: self.show_preview_changed.emit(state == Qt.CheckState.Checked.value)
        )
        layout.addWidget(self._preview_cb)

        layout.addSpacing(8)

        # Sharp handling
        sharp_row = QHBoxLayout()
        sharp_row.addWidget(QLabel("Sharp notes (15-key):"))
        self._sharp_combo = QComboBox()
        self._sharp_combo.addItems(["skip", "snap"])
        self._sharp_combo.setCurrentText(sharp_handling)
        self._sharp_combo.currentTextChanged.connect(self.sharp_handling_changed)
        if key_layout == KeyLayout.DRUMS:
            self._sharp_combo.setEnabled(False)
        sharp_row.addWidget(self._sharp_combo)
        layout.addLayout(sharp_row)

        layout.addSpacing(8)

        # Hotkeys section
        hotkey_label = QLabel("HOTKEYS")
        hotkey_label.setProperty("class", "overline")
        layout.addWidget(hotkey_label)

        # Play key
        play_row = QHBoxLayout()
        play_row.addWidget(QLabel("Play:"))
        self._play_key_label = QLabel(play_key.upper())
        self._play_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._play_key_label.setFixedWidth(90)
        self._play_key_label.setProperty("class", "key-badge")
        play_row.addWidget(self._play_key_label)
        play_bind_btn = QPushButton("Bind")
        play_bind_btn.setFixedWidth(50)
        play_bind_btn.setProperty("class", "ghost")
        play_bind_btn.clicked.connect(lambda: self._start_key_bind("play_key"))
        play_row.addWidget(play_bind_btn)
        layout.addLayout(play_row)

        # Stop key
        stop_row = QHBoxLayout()
        stop_row.addWidget(QLabel("Stop:"))
        self._stop_key_label = QLabel(stop_key.upper())
        self._stop_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stop_key_label.setFixedWidth(90)
        self._stop_key_label.setProperty("class", "key-badge")
        stop_row.addWidget(self._stop_key_label)
        stop_bind_btn = QPushButton("Bind")
        stop_bind_btn.setFixedWidth(50)
        stop_bind_btn.setProperty("class", "ghost")
        stop_bind_btn.clicked.connect(lambda: self._start_key_bind("stop_key"))
        stop_row.addWidget(stop_bind_btn)
        layout.addLayout(stop_row)

        # Emergency stop key
        emergency_row = QHBoxLayout()
        emergency_row.addWidget(QLabel("Emergency:"))
        self._emergency_key_label = QLabel(emergency_key.upper())
        self._emergency_key_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._emergency_key_label.setFixedWidth(90)
        self._emergency_key_label.setProperty("class", "key-badge")
        emergency_row.addWidget(self._emergency_key_label)
        emergency_bind_btn = QPushButton("Bind")
        emergency_bind_btn.setFixedWidth(50)
        emergency_bind_btn.setProperty("class", "ghost")
        emergency_bind_btn.clicked.connect(lambda: self._start_key_bind("emergency_stop_key"))
        emergency_row.addWidget(emergency_bind_btn)
        layout.addLayout(emergency_row)

        layout.addSpacing(8)

        # Demucs section
        demucs_label = QLabel("PIANO ISOLATION")
        demucs_label.setProperty("class", "overline")
        layout.addWidget(demucs_label)

        demucs_status_row = QHBoxLayout()
        self._demucs_status = QLabel(
            "Model: Installed" if demucs_available else "Model: Not installed"
        )
        self._demucs_status.setProperty("class", "caption")
        if demucs_available:
            self._demucs_status.setProperty("state", "finished")
        demucs_status_row.addWidget(self._demucs_status)
        demucs_status_row.addStretch()
        layout.addLayout(demucs_status_row)

        self._demucs_btn = QPushButton(
            "Remove Model" if demucs_available else "Download Model"
        )
        if demucs_available:
            self._demucs_btn.setProperty("class", "ghost")
        self._demucs_btn.clicked.connect(self._on_demucs_click)
        layout.addWidget(self._demucs_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "primary")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        if parent:
            center_dialog(self, parent)

    def _get_label_for_action(self, config_key: str) -> QLabel:
        """Get the key display label for a config key."""
        if config_key == "play_key":
            return self._play_key_label
        elif config_key == "stop_key":
            return self._stop_key_label
        else:
            return self._emergency_key_label

    def _start_key_bind(self, config_key: str) -> None:
        """Enter key-binding mode for the specified action."""
        self._listening_for = config_key
        label = self._get_label_for_action(config_key)
        label.setText("Press a key...")

    def keyPressEvent(self, event) -> None:
        """Handle key press for hotkey binding."""
        if self._listening_for is None:
            super().keyPressEvent(event)
            return

        qt_key = event.key()
        config_key = self._listening_for
        label = self._get_label_for_action(config_key)

        config_value = BINDABLE_KEYS_QT.get(qt_key)
        if config_value is None:
            # Unsupported key — revert
            current = getattr(self, f"_{config_key}", "")
            label.setText(current.upper() if current else "")
            self._listening_for = None
            return

        # Check for conflicts
        conflict = self._check_hotkey_conflict(config_value, config_key)
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
                self._play_key_label.setText("(unbound)")
            elif config_value == self._stop_key:
                self._stop_key_label.setText("(unbound)")
            elif config_value == self._emergency_key:
                self._emergency_key_label.setText("(unbound)")

        label.setText(config_value.upper())

        # Update internal state
        if config_key == "play_key":
            self._play_key = config_value
        elif config_key == "stop_key":
            self._stop_key = config_value
        elif config_key == "emergency_stop_key":
            self._emergency_key = config_value

        self.hotkey_changed.emit(config_key, config_value)
        self._listening_for = None

    def _check_hotkey_conflict(self, new_key: str, current_action: str) -> str | None:
        """Check if a key is already bound to another action.

        Returns:
            The name of the conflicting action, or None if no conflict.
        """
        if new_key == self._play_key and current_action != "play_key":
            return "Play"
        elif new_key == self._stop_key and current_action != "stop_key":
            return "Stop"
        elif new_key == self._emergency_key and current_action != "emergency_stop_key":
            return "Emergency Stop"
        return None

    def _on_demucs_click(self) -> None:
        """Handle demucs download/remove button click."""
        self.demucs_download_requested.emit()
