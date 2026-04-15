"""Modal dialog prompting the user to trim leading silence from flagged songs."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.theme import SPACING
from maestro.gui.utils import center_dialog


class LeadingSilenceDialog(QDialog):
    """Ask the user whether to trim leading silence from N flagged songs.

    Accepting returns ``QDialog.Accepted`` (1); Skip / close returns
    ``QDialog.Rejected`` (0). Callers distinguish via ``exec()`` return.
    """

    def __init__(self, count: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Trim leading silence?")
        self.setModal(True)
        self.setFixedSize(420, 180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING["lg"], SPACING["lg"], SPACING["lg"], SPACING["lg"]
        )
        layout.setSpacing(SPACING["md"])

        noun = "song" if count == 1 else "songs"
        message = (
            f"{count} {noun} start with more than 0.5 seconds of silence. "
            f"Trim them so they start promptly?\n\n"
            f"The files will be modified in place."
        )
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(msg_label, stretch=1)

        button_row = QHBoxLayout()
        button_row.setSpacing(SPACING["sm"])
        button_row.addStretch()

        self._skip_btn = QPushButton("Skip")
        self._skip_btn.setProperty("class", "ghost")
        self._skip_btn.clicked.connect(self.reject)
        button_row.addWidget(self._skip_btn)

        self._trim_btn = QPushButton("Trim all")
        self._trim_btn.setProperty("class", "primary")
        self._trim_btn.setDefault(True)
        self._trim_btn.clicked.connect(self.accept)
        button_row.addWidget(self._trim_btn)

        layout.addLayout(button_row)

        if parent is not None:
            center_dialog(self, parent)
