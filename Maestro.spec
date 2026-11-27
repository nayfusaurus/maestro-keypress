# -*- mode: python ; coding: utf-8 -*-
# SPDX-License-Identifier: MPL-2.0
"""
PyInstaller spec file for Maestro.

Build with: pyinstaller Maestro.spec
Output: dist/Maestro.exe
"""

from pathlib import Path
import os

# Get the project root
PROJ_ROOT = Path(SPECPATH)

# Bundle the app icon so Qt can set window/taskbar icon at runtime.
# The .spec icon= only embeds into the .exe for Windows Explorer;
# Qt needs the actual file to call QIcon() / setWindowIcon().
icon_data = [
    (str(PROJ_ROOT / 'assets' / 'icon.png'), 'assets'),
    (str(PROJ_ROOT / 'assets' / 'icon.ico'), 'assets'),
]

metrics_url = os.environ.get("MAESTRO_METRICS_URL", "").strip()
if metrics_url:
    if not metrics_url.startswith("https://") or not metrics_url.endswith("/report"):
        raise ValueError("MAESTRO_METRICS_URL must be an HTTPS /report URL")
    endpoint_file = Path(workpath) / "metrics_endpoint.txt"
    endpoint_file.parent.mkdir(parents=True, exist_ok=True)
    endpoint_file.write_text(metrics_url, encoding="utf-8")
    icon_data.append((str(endpoint_file), "maestro"))

a = Analysis(
    [str(PROJ_ROOT / 'src' / 'maestro' / 'main.py')],
    pathex=[str(PROJ_ROOT / 'src')],
    binaries=[],
    datas=icon_data,
    hiddenimports=[
        # --- App core ---
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # --- Unused Qt modules ---
        'tkinter',
        'PySide6.QtNetwork',
        'PySide6.QtQml',
        'PySide6.QtQuick',
        'PySide6.QtSvg',
        'PySide6.QtXml',
        'PySide6.Qt3DCore',
        'PySide6.QtMultimedia',
        'PySide6.QtWebEngine',

        # --- Dev/test tools ---
        'pytest',
        # NOTE: Do NOT exclude 'unittest' — onnxruntime imports it at runtime
        'IPython',
        'matplotlib',
        'sphinx',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Maestro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
