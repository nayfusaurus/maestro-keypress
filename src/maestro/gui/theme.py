"""Dark theme stylesheet for the Maestro GUI.

Design tokens and Catppuccin Mocha-inspired dark color palette with
tonal surface hierarchy, spacing scale, typographic scale, and
comprehensive QSS for all Qt widgets.
"""

from PySide6.QtWidgets import QApplication

# ---------------------------------------------------------------------------
# Design Tokens
# ---------------------------------------------------------------------------

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24, "2xl": 32}

RADIUS = {"sm": 4, "md": 8, "lg": 12}

FONT_FAMILY = '"Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif'

FONT = {
    "title": {"size": 14, "weight": 600},
    "body": {"size": 10, "weight": 400},
    "caption": {"size": 9, "weight": 400},
    "label": {"size": 8, "weight": 600},
    "overline": {"size": 7, "weight": 700},
}

# ---------------------------------------------------------------------------
# Color Palette — Catppuccin Mocha with tonal surface hierarchy
# ---------------------------------------------------------------------------

COLORS = {
    "base": "#1e1e2e",
    "surface0": "#232334",
    "surface1": "#2a2a3c",
    "surface2": "#313244",
    "surface_hover": "#3b3d52",
    "surface_active": "#45475a",
    "overlay": "#585b70",
    "subtext": "#6c7086",
    "text": "#cdd6f4",
    "text_dim": "#a6adc8",
    "accent": "#89b4fa",
    "accent_hover": "#a6c8ff",
    "accent_dim": "#5d7cbf",
    "green": "#a6e3a1",
    "green_dark": "#40a02b",
    "red": "#f38ba8",
    "red_dark": "#d32f2f",
    "yellow": "#f9e2af",
    "pending": "#6c7086",
    "link": "#89b4fa",
}

# ---------------------------------------------------------------------------
# Dark Theme QSS
# ---------------------------------------------------------------------------

DARK_THEME = f"""
/* ── Global ─────────────────────────────────────────────────────────── */

* {{
    font-family: {FONT_FAMILY};
}}

/* ── Top-level containers ───────────────────────────────────────────── */

QMainWindow, QDialog {{
    background-color: {COLORS["base"]};
    color: {COLORS["text"]};
}}

/* ── Labels ─────────────────────────────────────────────────────────── */

QLabel {{
    color: {COLORS["text"]};
}}

QLabel[class="caption"] {{
    color: {COLORS["subtext"]};
    font-size: 9pt;
}}

QLabel[class="overline"] {{
    color: {COLORS["overlay"]};
    font-size: 7pt;
    font-weight: 700;
}}

QLabel[class="title"] {{
    font-size: 14pt;
    font-weight: 600;
}}

QLabel[class="key-badge"] {{
    background-color: {COLORS["surface2"]};
    border: 1px solid {COLORS["surface_active"]};
    border-radius: 6px;
    padding: 4px 8px;
    font-weight: 600;
}}

QLabel[state="finished"] {{
    color: {COLORS["green"]};
}}

QLabel[state="error"] {{
    color: {COLORS["red"]};
    font-weight: 600;
}}

/* ── List Widget ────────────────────────────────────────────────────── */

QListWidget {{
    background-color: {COLORS["surface1"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface_active"]};
    border-radius: 8px;
    selection-background-color: {COLORS["surface_hover"]};
    selection-color: {COLORS["text"]};
    outline: none;
}}

QListWidget::item {{
    padding: 8px 12px;
}}

QListWidget::item:hover {{
    background-color: {COLORS["surface_hover"]};
}}

/* ── Push Buttons ───────────────────────────────────────────────────── */

QPushButton {{
    background-color: {COLORS["surface2"]};
    color: {COLORS["text"]};
    border: none;
    border-radius: 6px;
    padding: 6px 16px;
    min-height: 28px;
}}

QPushButton:hover {{
    background-color: {COLORS["surface_hover"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["surface_active"]};
}}

QPushButton:disabled {{
    background-color: {COLORS["surface1"]};
    color: {COLORS["subtext"]};
}}

QPushButton[class="primary"] {{
    background-color: {COLORS["accent"]};
    color: {COLORS["base"]};
    font-weight: 600;
    border: none;
}}

QPushButton[class="primary"]:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton[class="ghost"] {{
    background: transparent;
    border: none;
    border-radius: 6px;
}}

QPushButton[class="ghost"]:hover {{
    background-color: {COLORS["surface2"]};
}}

/* ── Combo Box ──────────────────────────────────────────────────────── */

QComboBox {{
    background-color: {COLORS["surface2"]};
    color: {COLORS["text"]};
    border: none;
    border-radius: 6px;
    padding: 6px 12px;
}}

QComboBox::drop-down {{
    border: none;
    width: 20px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {COLORS["text"]};
    margin-right: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {COLORS["surface1"]};
    color: {COLORS["text"]};
    selection-background-color: {COLORS["surface_hover"]};
    border: 1px solid {COLORS["surface2"]};
    outline: none;
}}

/* ── Slider ─────────────────────────────────────────────────────────── */

QSlider::groove:horizontal {{
    background: {COLORS["surface_active"]};
    height: 4px;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {COLORS["accent"]};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}

QSlider::handle:horizontal:hover {{
    background: {COLORS["accent_hover"]};
}}

/* ── Progress Bar ───────────────────────────────────────────────────── */

QProgressBar {{
    background-color: {COLORS["surface2"]};
    border: none;
    border-radius: 2px;
    min-height: 4px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {COLORS["accent"]};
    border-radius: 2px;
}}

/* ── Group Box ──────────────────────────────────────────────────────── */

QGroupBox {{
    border: none;
    color: {COLORS["text"]};
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
    background-color: {COLORS["surface1"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface2"]};
    border-radius: 6px;
    padding: 6px 12px;
    min-height: 28px;
}}

QLineEdit:focus {{
    border-color: {COLORS["accent"]};
}}

/* ── Menu Bar ───────────────────────────────────────────────────────── */

QMenuBar {{
    background-color: {COLORS["base"]};
    color: {COLORS["text"]};
    border-bottom: 1px solid {COLORS["surface2"]};
}}

QMenuBar::item {{
    padding: 6px 10px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS["surface_hover"]};
    border-radius: 4px;
}}

/* ── Menu ────────────────────────────────────────────────────────────── */

QMenu {{
    background-color: {COLORS["surface1"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface2"]};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS["surface_hover"]};
}}

QMenu::separator {{
    height: 1px;
    background: {COLORS["surface_active"]};
    margin: 4px 8px;
}}

/* ── Text Edit ──────────────────────────────────────────────────────── */

QTextEdit {{
    background-color: {COLORS["surface1"]};
    color: {COLORS["text"]};
    border: 1px solid {COLORS["surface2"]};
    border-radius: 8px;
}}

/* ── Check Box ──────────────────────────────────────────────────────── */

QCheckBox {{
    color: {COLORS["text"]};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {COLORS["overlay"]};
    border-radius: 4px;
    background-color: {COLORS["surface2"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

QCheckBox::indicator:hover {{
    border-color: {COLORS["accent"]};
}}

QCheckBox:disabled {{
    color: {COLORS["subtext"]};
}}

/* ── Scroll Bars ────────────────────────────────────────────────────── */

QScrollBar:vertical {{
    background: {COLORS["base"]};
    width: 6px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["overlay"]};
    border-radius: 3px;
    min-height: 20px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS["subtext"]};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}

QScrollBar:horizontal {{
    background: {COLORS["base"]};
    height: 6px;
}}

QScrollBar::handle:horizontal {{
    background: {COLORS["overlay"]};
    border-radius: 3px;
    min-width: 20px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {COLORS["subtext"]};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    height: 0px;
}}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: none;
}}

/* ── Semantic Widgets ───────────────────────────────────────────────── */

QWidget[class="surface-card"] {{
    background-color: {COLORS["surface0"]};
    border-radius: 8px;
}}

QFrame[class="banner"] {{
    background-color: {COLORS["surface0"]};
    border-radius: 8px;
    border: 1px solid {COLORS["surface2"]};
}}

/* ── Horizontal/Vertical Lines ──────────────────────────────────────── */

QFrame[frameShape="4"] {{
    color: {COLORS["surface_active"]};
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply the dark theme to the application."""
    app.setStyleSheet(DARK_THEME)
