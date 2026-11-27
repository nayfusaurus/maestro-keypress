# SPDX-License-Identifier: MPL-2.0
"""Shared privacy disclosure and versioned first-run consent."""

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.constants import DISCLAIMER_TEXT

CONSENT_VERSION = 1
DISCLOSURE = (
    "Maestro sends daily summaries to the developer via Cloudflare. They include a random "
    "installation ID, UTC activity date (including days you open Maestro without playing), "
    "app version, Windows version and build, keyboard input language, and approximate Maestro "
    "window size in 200-pixel ranges. Counts by game and instrument layout cover playback "
    "attempts, successful starts, completions, manual stops, input failures, unreadable files "
    "and songs with no playable notes. Cloudflare estimates country from the upload connection. "
    "The database stores country totals separately. Reports expire after 90 days. "
    "Song names, file paths, window titles and typed keys are excluded. "
    "Turn sharing off in Settings to stop reporting and erase pending summaries."
)


def show_example(parent: QWidget) -> None:
    QMessageBox.information(
        parent,
        "Example usage report",
        "Installation: random ID • UTC day: 2026-11-27 • Maestro: 2.1.0\n"
        "Windows 11 build 26100 • Keyboard: en-US • Window: 1000–1199 × 600–799\n"
        "Heartopia, 22-key: 2 attempts, 2 successful starts, 1 completion, 1 manual stop.\n\n"
        "Server-side only: one daily country count, e.g. Singapore. "
        "The country is separate from this installation’s report.",
    )


class WelcomeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Welcome to Maestro")
        self.resize(560, 570)
        layout = QVBoxLayout(self)
        terms = QTextBrowser()
        terms.setPlainText(DISCLAIMER_TEXT)
        layout.addWidget(terms)
        self.terms = QCheckBox("I accept the Maestro usage terms (required)")
        self.sharing = QCheckBox("Share usage statistics (optional, on by default)")
        self.sharing.setChecked(True)
        layout.addWidget(self.terms)
        layout.addWidget(self.sharing)
        details = QLabel(DISCLOSURE)
        details.setWordWrap(True)
        layout.addWidget(details)
        example = QPushButton("View an example report")
        example.clicked.connect(lambda: show_example(self))
        layout.addWidget(example)
        buttons = QDialogButtonBox()
        self.proceed = buttons.addButton(
            "Save choices and continue", QDialogButtonBox.ButtonRole.AcceptRole
        )
        buttons.addButton("Exit", QDialogButtonBox.ButtonRole.RejectRole)
        self.proceed.setEnabled(False)
        self.terms.toggled.connect(self.proceed.setEnabled)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


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
