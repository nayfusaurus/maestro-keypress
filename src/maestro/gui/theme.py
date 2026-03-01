"""Theme system for the Maestro GUI.

Supports dark (Catppuccin Mocha) and light (Catppuccin Latte) themes with
shared design tokens, tonal surface hierarchy, and comprehensive QSS.
"""

from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------------------------

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32}

RADIUS = {"sm": 4, "md": 8, "lg": 12}

FONT_FAMILY = '"Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif'

FONT = {
    "title": {"size": 19, "weight": 600},
    "body": {"size": 13, "weight": 400},
    "caption": {"size": 12, "weight": 400},
    "label": {"size": 11, "weight": 600},
    "overline": {"size": 10, "weight": 700},
}

# ---------------------------------------------------------------------------
# Color Palettes
# ---------------------------------------------------------------------------

DARK_COLORS = {
    "base": "#1e1e2e",
    "surface0": "#292940",
    "surface1": "#313244",
    "surface2": "#3b3d52",
    "surface_hover": "#45475a",
    "surface_active": "#585b70",
    "overlay": "#7f849c",
    "subtext": "#a6adc8",
    "text": "#cdd6f4",
    "text_dim": "#bac2de",
    "accent": "#89b4fa",
    "accent_hover": "#a6c8ff",
    "accent_dim": "#5d7cbf",
    "green": "#a6e3a1",
    "green_dark": "#40a02b",
    "red": "#f38ba8",
    "red_dark": "#d32f2f",
    "yellow": "#f9e2af",
    "pending": "#7f849c",
    "link": "#89b4fa",
}

LIGHT_COLORS = {
    "base": "#eff1f5",
    "surface0": "#ffffff",
    "surface1": "#e6e9ef",
    "surface2": "#ccd0da",
    "surface_hover": "#bcc0cc",
    "surface_active": "#acb0be",
    "overlay": "#9ca0b0",
    "subtext": "#6c6f85",
    "text": "#4c4f69",
    "text_dim": "#5c5f77",
    "accent": "#1e66f5",
    "accent_hover": "#1252cc",
    "accent_dim": "#7287fd",
    "green": "#40a02b",
    "green_dark": "#2d8a1f",
    "red": "#d20f39",
    "red_dark": "#b01030",
    "yellow": "#df8e1d",
    "pending": "#9ca0b0",
    "link": "#1e66f5",
}

# Mutable reference to current theme colors — updated by apply_theme().
# Other modules import this dict and read values during paint/layout,
# so they automatically pick up the active theme.
COLORS: dict[str, str] = dict(DARK_COLORS)

# ---------------------------------------------------------------------------
# QSS Builder
# ---------------------------------------------------------------------------


def _build_qss(c: dict[str, str]) -> str:
    """Build the complete QSS stylesheet from a color dict."""
    return f"""
/* ── Global ─────────────────────────────────────────────────────────── */

* {{
    font-family: {FONT_FAMILY};
    font-size: {FONT["body"]["size"]}pt;
}}

/* ── Top-level containers ───────────────────────────────────────────── */

QMainWindow, QDialog {{
    background-color: {c["base"]};
    color: {c["text"]};
}}

QWidget {{
    background-color: {c["base"]};
    color: {c["text"]};
}}

/* ── Labels ─────────────────────────────────────────────────────────── */

QLabel {{
    color: {c["text"]};
    font-size: {FONT["body"]["size"]}pt;
}}

QLabel[class="caption"] {{
    color: {c["subtext"]};
    font-size: {FONT["caption"]["size"]}pt;
}}

QLabel[class="overline"] {{
    color: {c["overlay"]};
    font-size: {FONT["overline"]["size"]}pt;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel[class="title"] {{
    font-size: {FONT["title"]["size"]}pt;
    font-weight: 600;
}}

QLabel[class="key-badge"] {{
    background-color: {c["surface2"]};
    border: 1px solid {c["surface_active"]};
    border-radius: 6px;
    padding: 4px 10px;
    font-weight: 600;
    font-size: {FONT["caption"]["size"]}pt;
}}

QLabel[state="finished"] {{
    color: {c["green"]};
}}

QLabel[state="error"] {{
    color: {c["red"]};
    font-weight: 600;
}}

/* ── List Widget ────────────────────────────────────────────────────── */

QListWidget {{
    background-color: {c["surface0"]};
    color: {c["text"]};
    border: 1px solid {c["surface_active"]};
    border-radius: 8px;
    selection-background-color: {c["surface_hover"]};
    selection-color: {c["text"]};
    outline: none;
    font-size: {FONT["body"]["size"]}pt;
}}

QListWidget::item {{
    padding: 8px 12px;
}}

QListWidget::item:hover {{
    background-color: {c["surface_hover"]};
}}

/* ── Push Buttons ───────────────────────────────────────────────────── */

QPushButton {{
    background-color: {c["surface2"]};
    color: {c["text"]};
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
    font-size: {FONT["body"]["size"]}pt;
}}

QPushButton:hover {{
    background-color: {c["surface_hover"]};
}}

QPushButton:pressed {{
    background-color: {c["surface_active"]};
}}

QPushButton:disabled {{
    background-color: {c["surface1"]};
    color: {c["subtext"]};
}}

QPushButton[class="primary"] {{
    background-color: {c["accent"]};
    color: {c["base"]};
    font-weight: 600;
    border: none;
}}

QPushButton[class="primary"]:hover {{
    background-color: {c["accent_hover"]};
}}

QPushButton[class="ghost"] {{
    background: transparent;
    border: none;
    border-radius: 6px;
}}

QPushButton[class="ghost"]:hover {{
    background-color: {c["surface2"]};
}}

/* ── Combo Box ──────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {c["surface2"]};
    color: {c["text"]};
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
    font-size: {FONT["body"]["size"]}pt;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {c["text"]};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {c["surface1"]};
    color: {c["text"]};
    selection-background-color: {c["surface_hover"]};
    border: 1px solid {c["surface2"]};
    outline: none;
}}

/* ── Slider ─────────────────────────────────────────────────────────── */

QSlider::groove:horizontal {{
    background: {c["surface_active"]};
    height: 4px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {c["accent"]};
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

QSlider::handle:horizontal:hover {{
    background: {c["accent_hover"]};
}}

/* ── Progress Bar ───────────────────────────────────────────────────── */

QProgressBar {{
    background-color: {c["surface2"]};
    border: none;
    border-radius: 2px;
    min-height: 4px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {c["accent"]};
    border-radius: 2px;
}}

/* ── Group Box ──────────────────────────────────────────────────────── */

QGroupBox {{
    border: none;
    color: {c["text"]};
    margin-top: 8px;
    padding-top: 16px;
    font-weight: bold;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}

/* ── Line Edit ──────────────────────────────────────────────────────── */

QLineEdit {{
    background-color: {c["surface1"]};
    color: {c["text"]};
    border: 1px solid {c["surface2"]};
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 28px;
    font-size: {FONT["body"]["size"]}pt;
}}

QLineEdit:focus {{
    border-color: {c["accent"]};
}}

/* ── Menu Bar ───────────────────────────────────────────────────────── */

QMenuBar {{
    background-color: {c["base"]};
    color: {c["text"]};
    border-bottom: 1px solid {c["surface2"]};
    font-size: {FONT["body"]["size"]}pt;
}}

QMenuBar::item {{
    padding: 6px 10px;
}}

QMenuBar::item:selected {{
    background-color: {c["surface_hover"]};
    border-radius: 4px;
}}

/* ── Menu ────────────────────────────────────────────────────────────── */

QMenu {{
    background-color: {c["surface0"]};
    color: {c["text"]};
    border: 1px solid {c["surface2"]};
    border-radius: 8px;
    padding: 4px;
    font-size: {FONT["body"]["size"]}pt;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {c["surface_hover"]};
}}

QMenu::separator {{
    height: 1px;
    background: {c["surface_active"]};
    margin: 4px 8px;
}}

/* ── Text Edit ──────────────────────────────────────────────────────── */

QTextEdit {{
    background-color: {c["surface1"]};
    color: {c["text"]};
    border: 1px solid {c["surface2"]};
    border-radius: 8px;
    font-size: {FONT["body"]["size"]}pt;
}}

/* ── Check Box ──────────────────────────────────────────────────────── */

QCheckBox {{
    color: {c["text"]};
    spacing: 8px;
    font-size: {FONT["body"]["size"]}pt;
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {c["overlay"]};
    border-radius: 4px;
    background-color: {c["surface2"]};
}}

QCheckBox::indicator:checked {{
    background-color: {c["accent"]};
    border-color: {c["accent"]};
}}

QCheckBox::indicator:hover {{
    border-color: {c["accent"]};
}}

QCheckBox:disabled {{
    color: {c["subtext"]};
}}

/* ── Scroll Area ───────────────────────────────────────────────────── */

QScrollArea {{
    background-color: {c["base"]};
    border: none;
}}

/* ── Scroll Bars ────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}

QScrollBar::handle:vertical {{
    background: {c["overlay"]};
    border-radius: 4px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {c["subtext"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 8px;
}}

QScrollBar::handle:horizontal {{
    background: {c["overlay"]};
    border-radius: 4px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {c["subtext"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    height: 0px;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ── Icon Rail ─────────────────────────────────────────────────────── */

IconRail {{
    background-color: {c["surface0"]};
    border-right: 1px solid {c["surface2"]};
}}

/* ── Semantic Widgets ───────────────────────────────────────────────── */

QWidget[class="surface-card"] {{
    background-color: {c["surface0"]};
    border: 1px solid {c["surface2"]};
    border-radius: 8px;
}}

QWidget[class="surface-card-flat"] {{
    background-color: transparent;
    border: none;
    border-radius: 0px;
}}

QFrame[class="banner"] {{
    background-color: {c["surface0"]};
    border-radius: 8px;
    border: 1px solid {c["surface2"]};
}}

/* ── Section heading (dimmer than overline, no letter-spacing) ────── */

QLabel[class="section-heading"] {{
    color: {c["subtext"]};
    font-size: {FONT["caption"]["size"]}pt;
    font-weight: 600;
}}

/* ── Separator line ─────────────────────────────────────────────────── */

QFrame[class="separator"] {{
    background-color: {c["surface2"]};
    max-height: 1px;
    min-height: 1px;
    margin: 6px 0px;
}}

/* ── Horizontal/Vertical Lines ──────────────────────────────────────── */

QFrame[frameShape="4"] {{
    color: {c["surface_active"]};
}}
"""


# Pre-built dark theme for backward compatibility
DARK_THEME = _build_qss(DARK_COLORS)

# Track current theme name
_current_theme: str = "dark"


def apply_theme(app: QApplication, dark: bool = True) -> None:
    """Apply the dark or light theme to the application."""
    global _current_theme
    source = DARK_COLORS if dark else LIGHT_COLORS
    COLORS.update(source)
    _current_theme = "dark" if dark else "light"
    app.setStyleSheet(_build_qss(source))


def is_dark_theme() -> bool:
    """Return True if the current theme is dark."""
    return _current_theme == "dark"
