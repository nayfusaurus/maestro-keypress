"""Exit confirmation dialog."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.utils import center_dialog


class ExitDialog(QDialog):
    """Modal confirmation dialog shown when the user attempts to close Maestro."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Exit Maestro")
        self.setFixedSize(320, 160)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        # Title
        title = QLabel("Exit Maestro?")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Body text
        body = QLabel("Are you sure you want to close the application?")
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        layout.addWidget(body)

        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self._cancel_btn)

        self._exit_btn = QPushButton("Exit")
        self._exit_btn.setProperty("class", "primary")
        self._exit_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self._exit_btn)

        layout.addLayout(btn_layout)

        if parent:
            center_dialog(self, parent)
