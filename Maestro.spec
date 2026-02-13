# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Maestro.

Build with: pyinstaller Maestro.spec
Output: dist/Maestro.exe
"""

import sys
from pathlib import Path

# Get the project root
PROJ_ROOT = Path(SPECPATH)

a = Analysis(
    [str(PROJ_ROOT / 'src' / 'maestro' / 'main.py')],
    pathex=[str(PROJ_ROOT / 'src')],
    binaries=[],
    datas=[],
    hiddenimports=[
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
