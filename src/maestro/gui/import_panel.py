"""Compact import panel for downloading songs from URLs."""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ImportPanel(QWidget):
    """Compact URL input bar for importing songs from YouTube.

    Layout:
      Row 1: [URL input (stretch)] [Import button]
      Row 2: [x] Isolate piano checkbox
      Row 3: Status label (hidden by default, shown during import)
    """

    import_clicked = Signal(str, bool)  # url, isolate_piano

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Row 1: URL input + Import button
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("Paste YouTube link...")
        self._url_input.returnPressed.connect(self._on_import_click)
        input_row.addWidget(self._url_input, stretch=1)

        self._import_btn = QPushButton("Import")
        self._import_btn.setProperty("class", "primary")
        self._import_btn.setFixedWidth(80)
        self._import_btn.clicked.connect(self._on_import_click)
        input_row.addWidget(self._import_btn)

        layout.addLayout(input_row)

        # Row 2: Isolate piano checkbox
        self._isolate_cb = QCheckBox(
            "Isolate piano (requires model \u2014 see Settings)"
        )
        self._isolate_cb.setEnabled(False)
        self._isolate_cb.setToolTip("Download model in Settings to enable")
        layout.addWidget(self._isolate_cb)

        # Row 3: Status label (hidden by default)
        self._status_label = QLabel()
        self._status_label.setProperty("class", "caption")
        self._status_label.setWordWrap(True)
        self._status_label.setVisible(False)
        layout.addWidget(self._status_label)

    def _on_import_click(self) -> None:
        url = self._url_input.text().strip()
        if url:
            self.import_clicked.emit(url, self._isolate_cb.isChecked())

    def get_url(self) -> str:
        """Return the current URL text, stripped of whitespace."""
        return self._url_input.text().strip()

    def show_progress(self, text: str) -> None:
        """Show progress text in subdued style."""
        self._status_label.setProperty("state", "")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
        self._status_label.setText(text)
        self._status_label.setVisible(True)

    def show_success(self, text: str) -> None:
        """Show success text in green (finished state)."""
        self._status_label.setProperty("state", "finished")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
        self._status_label.setText(text)
        self._status_label.setVisible(True)

    def show_error(self, text: str) -> None:
        """Show error text in red (error state)."""
        self._status_label.setProperty("state", "error")
        self._status_label.style().unpolish(self._status_label)
        self._status_label.style().polish(self._status_label)
        self._status_label.setText(text)
        self._status_label.setVisible(True)

    def clear_status(self) -> None:
        """Hide the status label and clear its text."""
        self._status_label.setVisible(False)
        self._status_label.setText("")

    def set_demucs_available(self, available: bool) -> None:
        """Enable or disable the isolate piano checkbox."""
        self._isolate_cb.setEnabled(available)
        if available:
            self._isolate_cb.setToolTip("")
        else:
            self._isolate_cb.setToolTip("Download model in Settings to enable")

    def set_importing(self, importing: bool) -> None:
        """Disable or enable the import button and URL input during import."""
        self._import_btn.setEnabled(not importing)
        self._url_input.setEnabled(not importing)
        if importing:
            self._import_btn.setToolTip("Import in progress")
        else:
            self._import_btn.setToolTip("")
            self._url_input.clear()
