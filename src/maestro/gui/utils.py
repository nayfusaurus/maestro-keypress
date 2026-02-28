"""Utility functions for the Maestro GUI."""

from pathlib import Path

from PySide6.QtWidgets import QDialog, QWidget


def get_songs_from_folder(folder: Path) -> list[Path]:
    """Get all MIDI files from a folder.

    Args:
        folder: Path to the songs folder

    Returns:
        List of paths to .mid and .midi files, sorted alphabetically
    """
    if not folder.exists():
        return []

    mid_files = list(folder.glob("*.mid"))
    midi_files = list(folder.glob("*.midi"))
    return sorted(mid_files + midi_files)


def format_time(seconds: float) -> str:
    """Format seconds as M:SS."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"


def center_dialog(dialog: QDialog, parent: QWidget) -> None:
    """Center a dialog on its parent window."""
    parent_geo = parent.geometry()
    dialog_geo = dialog.geometry()
    x = parent_geo.x() + (parent_geo.width() - dialog_geo.width()) // 2
    y = parent_geo.y() + (parent_geo.height() - dialog_geo.height()) // 2
    dialog.move(x, y)
