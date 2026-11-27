# SPDX-License-Identifier: MPL-2.0
"""Shared pytest configuration.

Sets QT_QPA_PLATFORM=offscreen before any Qt imports to avoid
platform plugin crashes in headless CI environments.
"""

import os
import sys
from unittest.mock import Mock

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(autouse=True)
def windows_keyboard_backend(monkeypatch):
    if sys.platform == "win32":

        monkeypatch.setattr("maestro.player.Controller", Mock())
        monkeypatch.setattr("maestro.player.pydirectinput", Mock())
        monkeypatch.setattr("maestro.player._foreground_window", lambda: (1, 123))
        monkeypatch.setattr("maestro.player._process_name", lambda pid: "xdt.exe")
