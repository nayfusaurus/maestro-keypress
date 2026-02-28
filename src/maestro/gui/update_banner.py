"""Dismissable update notification banner."""

import webbrowser

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from maestro.update_checker import UpdateInfo


class UpdateBanner(QFrame):
    """A dismissable banner that notifies the user of available updates."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._update_info: UpdateInfo | None = None
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setProperty("class", "banner")
        self.setVisible(False)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)

        self._message_label = QLabel()
        layout.addWidget(self._message_label, stretch=1)

        self._view_btn = QPushButton("View Release")
        self._view_btn.setProperty("class", "primary")
        self._view_btn.setFixedWidth(100)
        self._view_btn.clicked.connect(self._open_release_page)
        layout.addWidget(self._view_btn)

        self._dismiss_btn = QPushButton("Dismiss")
        self._dismiss_btn.setProperty("class", "ghost")
        self._dismiss_btn.setFixedWidth(70)
        self._dismiss_btn.clicked.connect(self.dismiss)
        layout.addWidget(self._dismiss_btn)

    def show_update(self, update_info: UpdateInfo) -> None:
        """Show the banner with update information."""
        self._update_info = update_info
        self._message_label.setText(
            f"Update available: v{update_info.latest_version}"
        )
        self.setVisible(True)

    def dismiss(self) -> None:
        """Hide the banner."""
        self.setVisible(False)
        self._update_info = None

    def _open_release_page(self) -> None:
        """Open the GitHub release page in the browser."""
        if self._update_info and self._update_info.release_url:
            webbrowser.open(self._update_info.release_url)
