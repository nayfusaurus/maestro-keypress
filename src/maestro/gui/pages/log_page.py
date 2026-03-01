"""Error Log page with built-in log viewer.

Displays the application log file in a read-only monospace text viewer
with refresh and open-in-editor capabilities.
"""

from PySide6.QtGui import QFont, QShowEvent, QTextCursor
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTextEdit, QVBoxLayout, QWidget

from maestro.gui.theme import SPACING
from maestro.logger import get_log_path, open_log_file


class LogPage(QWidget):
    """Page widget for viewing the application error log."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build the page layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACING["xl"], SPACING["md"], SPACING["xl"], SPACING["md"])
        layout.setSpacing(SPACING["md"])

        # --- Header row ---
        header = QHBoxLayout()
        header.setSpacing(8)

        title = QLabel("ERROR LOG")
        title.setProperty("class", "title")
        header.addWidget(title)

        header.addStretch()

        self._open_btn = QPushButton("Open in Editor")
        self._open_btn.setProperty("class", "ghost")
        self._open_btn.clicked.connect(open_log_file)
        header.addWidget(self._open_btn)

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self.load_log)
        header.addWidget(self._refresh_btn)

        layout.addLayout(header)

        # --- Log viewer ---
        self._log_viewer = QTextEdit()
        self._log_viewer.setReadOnly(True)
        self._log_viewer.setProperty("class", "surface-card")

        mono_font = QFont()
        mono_font.setStyleHint(QFont.StyleHint.Monospace)
        mono_font.setFamily("monospace")
        self._log_viewer.setFont(mono_font)

        layout.addWidget(self._log_viewer)

    def load_log(self) -> None:
        """Read the log file from disk and display its contents."""
        log_path = get_log_path()
        if log_path.exists() and log_path.stat().st_size > 0:
            text = log_path.read_text(encoding="utf-8", errors="replace")
            self._log_viewer.setPlainText(text)
        else:
            self._log_viewer.setPlainText("No log entries")

        # Auto-scroll to bottom
        cursor = self._log_viewer.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._log_viewer.setTextCursor(cursor)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        """Auto-load log contents when the page becomes visible."""
        super().showEvent(event)
        self.load_log()
