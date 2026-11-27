# SPDX-License-Identifier: MPL-2.0
"""Info page with About section and Disclaimer.

Combines the About card (app info, credits, Ko-fi link) and the Disclaimer
card (scrollable text, optional first-launch accept/reject flow) into a
single vertically-stacked page widget.
"""

from urllib.parse import urlencode

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.constants import APP_VERSION, DISCLAIMER_TEXT, GITHUB_REPO, KOFI_URL
from maestro.gui.theme import SPACING


class InfoPage(QWidget):
    """Info page containing About and Disclaimer cards.

    Parameters
    ----------
    first_launch : bool
        When ``True``, the disclaimer card shows accept/reject buttons and
        a prompt asking the user to read and accept. When ``False`` (the
        default), the disclaimer is shown as a read-only reference with no
        action buttons.
    parent : QWidget | None
        Optional parent widget.
    """

    disclaimer_accepted = Signal()
    disclaimer_rejected = Signal()

    def __init__(self, first_launch: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        about = QWidget()
        about.setProperty("class", "surface-card")
        about_layout = QVBoxLayout(about)
        about_layout.setContentsMargins(16, 12, 16, 12)
        header = QHBoxLayout()
        logo = QLabel()
        icon = self.windowIcon()
        if not icon.isNull():
            logo.setPixmap(icon.pixmap(48, 48))
            header.addWidget(logo)
        title = QLabel("Maestro")
        title.setProperty("class", "title")
        header.addWidget(title)
        self._version_label = QLabel(f"v{APP_VERSION}")
        self._version_label.setProperty("class", "caption")
        header.addWidget(self._version_label)
        header.addStretch()
        about_layout.addLayout(header)
        description = QLabel(
            "Play MIDI files in games with keyboard instruments. Created by nayfusaurus."
        )
        description.setWordWrap(True)
        about_layout.addWidget(description)

        links = QHBoxLayout()
        source = QPushButton("Source code · MPL 2.0")
        source.clicked.connect(lambda: self._open_link(f"https://github.com/{GITHUB_REPO}"))
        support = QPushButton("Support on Ko-fi")
        support.clicked.connect(lambda: self._open_link(KOFI_URL))
        links.addWidget(source)
        links.addWidget(support)
        links.addStretch()
        about_layout.addLayout(links)
        layout.addWidget(about)

        feedback = QWidget()
        feedback.setProperty("class", "surface-card")
        feedback_layout = QVBoxLayout(feedback)
        heading = QLabel("Feedback")
        heading.setProperty("class", "section-heading")
        feedback_layout.addWidget(heading)
        note = QLabel(
            "Opens a public GitHub issue form in your browser. Sign in to submit. "
            "Leave out personal details and credentials."
        )
        note.setWordWrap(True)
        note.setProperty("class", "caption")
        feedback_layout.addWidget(note)
        actions = QHBoxLayout()
        bug = QPushButton("Report a bug")
        bug.clicked.connect(
            lambda: self._open_feedback(
                "Bug",
                "### What happened?\n\n"
                "### Steps to reproduce\n\n### Expected result\n\n"
                f"### Maestro version\n{APP_VERSION}",
            )
        )
        suggestion = QPushButton("Suggest a feature")
        suggestion.clicked.connect(
            lambda: self._open_feedback(
                "Suggestion", "### What would you like to do?\n\n### How would this help?\n"
            )
        )
        actions.addWidget(bug)
        actions.addWidget(suggestion)
        actions.addStretch()
        feedback_layout.addLayout(actions)
        layout.addWidget(feedback)

        disclaimer_card = QWidget()
        disclaimer_card.setProperty("class", "surface-card")
        disclaimer_layout = QVBoxLayout(disclaimer_card)
        heading_label = QLabel("Usage disclaimer")
        heading_label.setProperty("class", "section-heading")
        disclaimer_layout.addWidget(heading_label)
        self._disclaimer_text = QTextEdit()
        self._disclaimer_text.setPlainText(DISCLAIMER_TEXT)
        self._disclaimer_text.setAccessibleName("Usage disclaimer")
        self._disclaimer_text.setReadOnly(True)
        disclaimer_layout.addWidget(self._disclaimer_text, stretch=1)

        # First-launch prompt
        self._prompt_label = QLabel("Please read and accept to continue.")
        self._prompt_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        disclaimer_layout.addWidget(self._prompt_label)

        # Accept / Reject buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING["sm"])

        self._accept_btn = QPushButton("Accept")
        self._accept_btn.setProperty("class", "primary")
        self._accept_btn.clicked.connect(self._on_accept)
        btn_row.addWidget(self._accept_btn)

        self._reject_btn = QPushButton("Reject")
        btn_row.addWidget(self._reject_btn)
        self._reject_btn.clicked.connect(self._on_reject)

        self._btn_container = QWidget()
        self._btn_container.setLayout(btn_row)
        disclaimer_layout.addWidget(self._btn_container)

        layout.addWidget(disclaimer_card, stretch=1)

        # Show/hide first-launch elements
        if not first_launch:
            self._prompt_label.hide()
            self._accept_btn.hide()
            self._reject_btn.hide()
            self._btn_container.hide()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

    def _open_link(self, address: str) -> None:
        if not QDesktopServices.openUrl(QUrl(address)):
            QMessageBox.warning(self, "Browser unavailable", "Maestro could not open your browser.")

    def _open_feedback(self, category: str, prompts: str) -> None:
        # Only fixed prompts enter the URL. Users write and submit their report on GitHub.
        query = urlencode({"title": f"[{category}] ", "body": prompts})
        self._open_link(f"https://github.com/{GITHUB_REPO}/issues/new?{query}")

    def _on_accept(self) -> None:
        """Handle accept button click."""
        self._prompt_label.hide()
        self._accept_btn.hide()
        self._reject_btn.hide()
        self._btn_container.hide()
        self.disclaimer_accepted.emit()

    def _on_reject(self) -> None:
        """Handle reject button click."""
        self.disclaimer_rejected.emit()
