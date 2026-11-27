# SPDX-License-Identifier: MPL-2.0
"""Tests for the logger module."""

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

import maestro.logger
from maestro.logger import get_log_path, open_log_file, setup_logger


@pytest.fixture(autouse=True)
def reset_logger():
    """Reset the module-level _logger before each test."""
    maestro.logger._logger = None
    yield
    maestro.logger._logger = None


class TestGetLogPath:
    """Tests for get_log_path function."""

    def test_packaged_copy_starts_fresh_and_relaunch_keeps_log(self, tmp_path, monkeypatch):
        first = tmp_path / "first.exe"
        second = tmp_path / "second.exe"
        first.write_bytes(b"same build")
        second.write_bytes(first.read_bytes())
        monkeypatch.setattr(maestro.logger, "get_config_dir", lambda: tmp_path)
        monkeypatch.setattr(maestro.logger.sys, "frozen", True, raising=False)
        monkeypatch.setattr(maestro.logger.sys, "executable", str(first))
        original = get_log_path()
        original.parent.mkdir(parents=True)
        original.write_text("first copy")
        assert get_log_path().read_text() == "first copy"
        monkeypatch.setattr(maestro.logger.sys, "executable", str(second))
        assert get_log_path() != original
        assert not get_log_path().exists()

    def test_get_log_path_in_config_dir(self):
        """Log path should be maestro.log inside config directory."""
        with patch("maestro.logger.get_config_dir", return_value=Path("/test/config")):
            log_path = get_log_path()
            assert log_path == Path("/test/config") / "maestro.log"

class TestSetupLogger:
    """Tests for setup_logger function."""

    def test_setup_logger_returns_named_logger(self, tmp_path):
        """setup_logger should return logger with name 'maestro'."""
        with patch("maestro.logger.get_log_path", return_value=tmp_path / "maestro.log"):
            logger = setup_logger()
            assert logger.name == "maestro"

    def test_setup_logger_sets_debug_level(self, tmp_path):
        """Logger should be set to DEBUG level."""
        with patch("maestro.logger.get_log_path", return_value=tmp_path / "maestro.log"):
            logger = setup_logger()
            assert logger.level == logging.DEBUG

    def test_setup_logger_is_idempotent(self, tmp_path):
        """Calling setup_logger twice should return the same logger."""
        with patch("maestro.logger.get_log_path", return_value=tmp_path / "maestro.log"):
            logger1 = setup_logger()
            logger2 = setup_logger()
            assert logger1 is logger2

    def test_setup_logger_creates_directory(self, tmp_path):
        """setup_logger should create log directory if it doesn't exist."""
        log_path = tmp_path / "nested" / "dir" / "maestro.log"
        with patch("maestro.logger.get_log_path", return_value=log_path):
            setup_logger()
            assert log_path.parent.exists()

    def test_setup_logger_has_handler(self, tmp_path):
        """Logger should have at least one handler after setup."""
        with patch("maestro.logger.get_log_path", return_value=tmp_path / "maestro.log"):
            logger = setup_logger()
            assert len(logger.handlers) > 0


class TestOpenLogFile:
    """Tests for open_log_file function."""

    def test_open_log_file_does_nothing_if_no_file(self, tmp_path):
        """open_log_file should do nothing if log file doesn't exist."""
        log_path = tmp_path / "nonexistent.log"
        with (
            patch("maestro.logger.get_log_path", return_value=log_path),
            patch("maestro.logger.subprocess.run") as mock_run,
            patch("maestro.logger.os.startfile", create=True) as mock_startfile,
        ):
            open_log_file()
            mock_run.assert_not_called()
            mock_startfile.assert_not_called()

    def test_open_log_file_windows(self, tmp_path):
        """On Windows, should use os.startfile."""
        log_path = tmp_path / "maestro.log"
        log_path.touch()

        with (
            patch("maestro.logger.get_log_path", return_value=log_path),
            patch("maestro.logger.sys.platform", "win32"),
            patch("maestro.logger.os.startfile", create=True) as mock_startfile,
        ):
            open_log_file()
            mock_startfile.assert_called_once_with(log_path)

    def test_open_log_file_macos(self, tmp_path):
        """On macOS, should use 'open' command."""
        log_path = tmp_path / "maestro.log"
        log_path.touch()

        with (
            patch("maestro.logger.get_log_path", return_value=log_path),
            patch("maestro.logger.sys.platform", "darwin"),
            patch("maestro.logger.subprocess.run") as mock_run,
        ):
            open_log_file()
            mock_run.assert_called_once_with(["open", str(log_path)])

    def test_open_log_file_linux(self, tmp_path):
        """On Linux, should use 'xdg-open' command."""
        log_path = tmp_path / "maestro.log"
        log_path.touch()

        with (
            patch("maestro.logger.get_log_path", return_value=log_path),
            patch("maestro.logger.sys.platform", "linux"),
            patch("maestro.logger.subprocess.run") as mock_run,
        ):
            open_log_file()
            mock_run.assert_called_once_with(["xdg-open", str(log_path)])


def test_prune_and_clear_all_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(maestro.logger, "get_config_dir", lambda: tmp_path)
    for i in range(5):
        directory = tmp_path / "logs" / f"{i:024x}"
        directory.mkdir(parents=True)
        (directory / "maestro.log").write_text("old")
    active = directory / "maestro.log"
    monkeypatch.setattr(maestro.logger, "get_log_path", lambda: active)
    maestro.logger._prune_old_logs(active)
    assert len(list((tmp_path / "logs").iterdir())) == 3
    other = active.parent / "unrelated.txt"
    other.write_text("keep")
    maestro.logger.clear_all_logs()
    assert active.read_text() == ""
    assert other.read_text() == "keep"
    assert list((tmp_path / "logs").iterdir()) == [active.parent]
