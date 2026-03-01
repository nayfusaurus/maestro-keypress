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


def check_hotkey_conflict(
    new_key: str,
    current_action: str,
    play_key: str,
    stop_key: str,
    emergency_key: str,
) -> str | None:
    """Check if a key is already bound to another action.

    Returns:
        The name of the conflicting action, or None if no conflict.
    """
    if new_key == play_key and current_action != "play_key":
        return "Play"
    elif new_key == stop_key and current_action != "stop_key":
        return "Stop"
    elif new_key == emergency_key and current_action != "emergency_stop_key":
        return "Emergency Stop"
    return None
