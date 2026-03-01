"""Info page with About section and Disclaimer.

Combines the About card (app info, credits, Ko-fi link) and the Disclaimer
card (scrollable text, optional first-launch accept/reject flow) into a
single vertically-stacked page widget.
"""

import webbrowser

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from maestro.gui.constants import APP_VERSION, DISCLAIMER_TEXT, KOFI_URL
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

    def __init__(
        self, first_launch: bool = False, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._first_launch = first_launch

        outer = QHBoxLayout(self)
        outer.setContentsMargins(SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"])

        # Center the container horizontally using stretches, allow vertical fill
        outer.addStretch()
        container = QWidget()
        container.setMaximumWidth(560)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(SPACING["lg"])

        # --- About card ---
        about_card = QWidget()
        about_card.setProperty("class", "surface-card")
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        about_layout.setSpacing(SPACING["sm"])

        # Title
        title_label = QLabel("Maestro")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setProperty("class", "title")
        about_layout.addWidget(title_label)

        # Version
        self._version_label = QLabel(f"v{APP_VERSION}")
        self._version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._version_label.setProperty("class", "caption")
        about_layout.addWidget(self._version_label)

        # Description
        desc_label = QLabel("MIDI Piano Player for Games")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setProperty("class", "caption")
        about_layout.addWidget(desc_label)

        about_layout.addSpacing(SPACING["xs"])

        # Credits
        credits_label = QLabel("Created by nayfusaurus")
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        about_layout.addWidget(credits_label)

        about_layout.addSpacing(SPACING["md"])

        # Ko-fi button
        kofi_btn = QPushButton("Support on Ko-fi")
        kofi_btn.setProperty("class", "primary")
        kofi_btn.clicked.connect(lambda: webbrowser.open(KOFI_URL))
        about_layout.addWidget(kofi_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(about_card)

        # --- Disclaimer card ---
        disclaimer_card = QWidget()
        disclaimer_card.setProperty("class", "surface-card")
        disclaimer_layout = QVBoxLayout(disclaimer_card)
        disclaimer_layout.setContentsMargins(
            SPACING["xl"], SPACING["xl"], SPACING["xl"], SPACING["xl"]
        )
        disclaimer_layout.setSpacing(SPACING["md"])

        # Section heading
        heading_label = QLabel("Disclaimer")
        heading_label.setProperty("class", "section-heading")
        disclaimer_layout.addWidget(heading_label)

        # Scrollable disclaimer text
        self._disclaimer_text = QTextEdit()
        self._disclaimer_text.setPlainText(DISCLAIMER_TEXT)
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

        outer.addWidget(container)
        outer.addStretch()

        # Show/hide first-launch elements
        if not first_launch:
            self._prompt_label.hide()
            self._accept_btn.hide()
            self._reject_btn.hide()
            self._btn_container.hide()

    # ------------------------------------------------------------------
    # Slots
    # ------------------------------------------------------------------

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
