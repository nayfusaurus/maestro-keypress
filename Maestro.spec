# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Maestro.

Build with: pyinstaller Maestro.spec
Output: dist/Maestro.exe

ML Backend: ONNX Runtime (not TensorFlow). basic-pitch auto-detects
the ONNX backend when TF is excluded from the bundle.

Note: pyinstaller-hooks-contrib provides hooks for most deps (onnxruntime,
cv2, librosa, resampy, numba, llvmlite, sklearn, scipy, soundfile).
We only need manual hiddenimports for packages WITHOUT hooks.
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

# Get the project root
PROJ_ROOT = Path(SPECPATH)

# Collect basic-pitch model files (nmp.onnx, nmp.tflite, saved_model.pb)
# This is CRITICAL — without it, basic-pitch can't find its trained model.
# No hook exists for basic-pitch, so we must collect manually.
bp_data = collect_data_files('basic_pitch')

# Collect ffmpeg/ffprobe binaries if present in assets/ffmpeg/
# These are placed next to the exe so yt-dlp can find them.
ffmpeg_dir = PROJ_ROOT / 'assets' / 'ffmpeg'
ffmpeg_binaries = []
if ffmpeg_dir.is_dir():
    for name in ['ffmpeg.exe', 'ffprobe.exe', 'ffmpeg', 'ffprobe']:
        p = ffmpeg_dir / name
        if p.exists():
            ffmpeg_binaries.append((str(p), '.'))
    if not ffmpeg_binaries:
        print('WARNING: assets/ffmpeg/ exists but no ffmpeg binaries found!')
else:
    print('')
    print('ERROR: assets/ffmpeg/ not found — YouTube import will not work!')
    print('       Run first:  python scripts/download_ffmpeg.py')
    print('')
    sys.exit(1)

a = Analysis(
    [str(PROJ_ROOT / 'src' / 'maestro' / 'main.py')],
    pathex=[str(PROJ_ROOT / 'src')],
    binaries=ffmpeg_binaries,
    datas=bp_data,
    hiddenimports=[
        # --- App core ---
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',

        # --- Import pipeline ---
        'yt_dlp',

        # --- Packages WITHOUT pyinstaller-hooks-contrib hooks ---
        # (cv2, librosa, resampy, numba, llvmlite, sklearn, scipy,
        #  soundfile, onnxruntime all have hooks that auto-collect)
        'basic_pitch',
        'basic_pitch.inference',
        'basic_pitch.note_creation',
        'basic_pitch.constants',
        'basic_pitch.commandline_printing',
        'basic_pitch.nn',
        'pretty_midi',
        'mir_eval',
        'audioread',
        'lazy_loader',
        'soxr',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # --- Remove full TensorFlow (use ONNX instead) ---
        # On Windows, TF 2.14 is a meta-package that installs tensorflow-intel.
        # Both must be excluded to prevent bundling ~1.5GB of TF code.
        'tensorflow',
        'tensorflow_intel',
        'tensorflow_estimator',
        'tensorflow_io_gcs_filesystem',
        'tensorboard',
        'tensorboard_data_server',
        'keras',
        'h5py',
        'grpcio',
        'google.protobuf',
        'absl',
        'astunparse',
        'gast',
        'opt_einsum',
        'pasta',
        'termcolor',
        'wrapt',
        'libclang',
        'ml_dtypes',

        # --- CoreML (macOS only, not needed) ---
        'coremltools',

        # --- TFLite (not using this backend) ---
        'tflite_runtime',

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
