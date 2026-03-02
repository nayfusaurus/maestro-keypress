"""Shared pytest configuration.

Sets QT_QPA_PLATFORM=offscreen before any Qt imports to avoid
platform plugin crashes in headless CI environments.
"""

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
