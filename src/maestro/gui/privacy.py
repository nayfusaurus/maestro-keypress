# SPDX-License-Identifier: MPL-2.0
"""Shared privacy disclosure and versioned first-run consent."""

from math import ceil

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.constants import DISCLAIMER_TEXT
from maestro.gui.theme import COLORS

CONSENT_VERSION = 1
DISCLOSURE = (
    "Maestro sends a daily summary when you use the app, including days without playback. "
    "It includes a random installation ID, activity date, app and Windows versions, keyboard "
    "language, approximate window size, and playback counts by game and layout. "
    "You can turn sharing off in Settings."
)


def show_privacy_text(parent: QWidget, title: str, text: str) -> None:
    dialog = QDialog(parent)
    dialog.setObjectName("privacyDialog")
    dialog.setWindowTitle(title)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(14)
    heading = QLabel(title)
    heading.setProperty("class", "title")
    layout.addWidget(heading)
    body = QTextBrowser()
    body.setAccessibleName(title)
    body.setPlainText(text)
    layout.addWidget(body)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    available = parent.screen().availableGeometry()
    width = min(540, available.width() - 32)
    body.ensurePolished()
    body.document().setDefaultFont(body.font())
    body.document().setTextWidth(width - 100)
    height = (
        ceil(body.document().size().height())
        + heading.sizeHint().height()
        + buttons.sizeHint().height()
        + 90
    )
    dialog.resize(width, min(max(300, height + 42), available.height() - 80))
    dialog.exec()
    dialog.deleteLater()


def show_example(parent: QWidget) -> None:
    show_privacy_text(
        parent,
        "Example usage report",
        "Installation: random ID • UTC day: 2026-11-27 • Maestro: 2.1.0\n"
        "Windows 11 build 26100 • Keyboard: en-US • Window: 1000–1199 × 600–799\n"
        "Heartopia, 22-key: 2 attempts, 2 successful starts, 1 completion, 1 manual stop.",
    )


class WelcomeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome to Maestro")
        self.setObjectName("welcomeDialog")
        self.setStyleSheet(
            f"QDialog#welcomeDialog {{ background-color: {COLORS['base']}; }}"
            "QLabel, QCheckBox, QPushButton { font-size: 14px; }"
            "QLabel#heading { font-size: 24px; font-weight: 600; }"
            "QCheckBox::indicator:checked { background-color: white;"
            " image: url(:/qt-project.org/styles/commonstyle/images/standardbutton-apply-16.png); }"
            f"QLabel#details {{ color: {COLORS['text_dim']}; }}"
            f"QPushButton[flat='true'] {{ color: {COLORS['link']}; background: transparent;"
            " padding: 2px 4px; min-height: 22px; }"
            "QPushButton[flat='true']:hover { text-decoration: underline; }"
            f"QPushButton#continueButton:disabled {{ background: {COLORS['surface2']};"
            f" color: {COLORS['text_dim']}; }}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 20)
        layout.setSpacing(10)
        heading = QLabel("Welcome to Maestro")
        heading.setObjectName("heading")
        layout.addWidget(heading)
        summary = QLabel(
            "Maestro simulates keyboard input. Check your game’s rules before using it."
        )
        summary.setWordWrap(True)
        layout.addWidget(summary)
        terms_row = QHBoxLayout()
        self.terms = QCheckBox("I accept the usage terms")
        terms_row.addWidget(self.terms)
        terms_row.addStretch()
        read_terms = QPushButton("Read usage terms")
        read_terms.setFlat(True)
        read_terms.clicked.connect(lambda: show_privacy_text(self, "Usage terms", DISCLAIMER_TEXT))
        terms_row.addWidget(read_terms)
        layout.addLayout(terms_row)
        layout.addSpacing(8)
        self.sharing = QCheckBox("Share usage statistics (optional)")
        self.sharing.setChecked(True)
        layout.addWidget(self.sharing)
        details = QLabel(DISCLOSURE)
        details.setObjectName("details")
        details.setWordWrap(True)
        layout.addWidget(details)
        example = QPushButton("View example report")
        example.setFlat(True)
        example.clicked.connect(lambda: show_example(self))
        layout.addWidget(example, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addStretch()
        layout.addSpacing(8)
        buttons = QDialogButtonBox()
        self.proceed = buttons.addButton("Continue", QDialogButtonBox.ButtonRole.AcceptRole)
        self.proceed.setObjectName("continueButton")
        self.proceed.setProperty("class", "primary")
        buttons.addButton("Exit", QDialogButtonBox.ButtonRole.RejectRole)
        self.proceed.setEnabled(False)
        self.terms.toggled.connect(self.proceed.setEnabled)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.resize(520, layout.totalHeightForWidth(520))


def review_choices(config: dict) -> bool:
    """Apply a confirmed decision. Closing without acceptance leaves config untouched."""
    if (
        config.get("privacy_version") == CONSENT_VERSION
        and config.get("disclaimer_accepted") is True
    ):
        return True
    dialog = WelcomeDialog()
    if not dialog.exec():
        return False
    config.update(
        disclaimer_accepted=True,
        privacy_version=CONSENT_VERSION,
        share_usage=dialog.sharing.isChecked(),
    )
    return True
