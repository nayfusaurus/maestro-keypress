"""Constants for the Maestro GUI."""

from PySide6.QtCore import Qt

# App info
APP_VERSION = "1.5.0"
GITHUB_REPO = "nayfusaurus/maestro-keypress"
KOFI_URL = "https://ko-fi.com/nayfusaurus"

# Valid key names that can be bound (maps tkinter keysym to config key name)
# Kept for backwards compatibility with existing config files
BINDABLE_KEYS = {
    "F1": "f1",
    "F2": "f2",
    "F3": "f3",
    "F4": "f4",
    "F5": "f5",
    "F6": "f6",
    "F7": "f7",
    "F8": "f8",
    "F9": "f9",
    "F10": "f10",
    "F11": "f11",
    "F12": "f12",
    "Escape": "escape",
    "Home": "home",
    "End": "end",
    "Insert": "insert",
    "Delete": "delete",
    "Prior": "page_up",
    "Next": "page_down",
}

# Maps Qt key codes to config key names
BINDABLE_KEYS_QT: dict[int, str] = {
    Qt.Key.Key_F1: "f1",
    Qt.Key.Key_F2: "f2",
    Qt.Key.Key_F3: "f3",
    Qt.Key.Key_F4: "f4",
    Qt.Key.Key_F5: "f5",
    Qt.Key.Key_F6: "f6",
    Qt.Key.Key_F7: "f7",
    Qt.Key.Key_F8: "f8",
    Qt.Key.Key_F9: "f9",
    Qt.Key.Key_F10: "f10",
    Qt.Key.Key_F11: "f11",
    Qt.Key.Key_F12: "f12",
    Qt.Key.Key_Escape: "escape",
    Qt.Key.Key_Home: "home",
    Qt.Key.Key_End: "end",
    Qt.Key.Key_Insert: "insert",
    Qt.Key.Key_Delete: "delete",
    Qt.Key.Key_PageUp: "page_up",
    Qt.Key.Key_PageDown: "page_down",
}

# Disclaimer text
DISCLAIMER_TEXT = (
    "This software simulates keyboard input to interact with games. "
    "By using this tool, you acknowledge the following:\n\n"
    "1. USE AT YOUR OWN RISK. The developers are not responsible for "
    "any consequences, including but not limited to game bans or "
    "account suspensions.\n\n"
    "2. This tool is intended for personal, non-competitive use only. "
    "Using keyboard automation in games may violate the game's Terms "
    "of Service.\n\n"
    "3. Always check the game's policies regarding third-party tools "
    "and keyboard automation before use.\n\n"
    '4. This software is provided "as is" without warranty of any kind.'
)
