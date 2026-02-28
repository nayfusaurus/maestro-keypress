"""About and Disclaimer dialogs."""

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.constants import APP_VERSION, DISCLAIMER_TEXT, KOFI_URL
from maestro.gui.utils import center_dialog


class AboutDialog(QDialog):
    """About dialog showing app info, credits, and support link."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("About Maestro")
        self.setFixedSize(320, 300)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(8)

        # Title
        title = QLabel("Maestro")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Version
        version = QLabel(f"Version {APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        # Description
        desc = QLabel("MIDI Piano Player for Games")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setProperty("class", "caption")
        layout.addWidget(desc)

        layout.addSpacing(5)

        # Credits
        credits = QLabel("Created by nayfusaurus")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits)

        layout.addSpacing(16)

        # Support section
        support = QLabel("Like this tool? Support development:")
        support.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(support)

        kofi_btn = QPushButton("Buy me a coffee on Ko-fi")
        kofi_btn.setProperty("class", "primary")
        kofi_btn.clicked.connect(lambda: webbrowser.open(KOFI_URL))
        layout.addWidget(kofi_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        if parent:
            center_dialog(self, parent)


class DisclaimerDialog(QDialog):
    """Disclaimer / Terms of Service dialog."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Disclaimer")
        self.setFixedSize(420, 320)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)

        # Title
        title = QLabel("Disclaimer")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setProperty("class", "title")
        layout.addWidget(title)

        # Disclaimer text
        text_widget = QTextEdit()
        text_widget.setPlainText(DISCLAIMER_TEXT)
        text_widget.setReadOnly(True)
        layout.addWidget(text_widget)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "primary")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        if parent:
            center_dialog(self, parent)
