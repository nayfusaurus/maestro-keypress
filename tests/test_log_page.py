"""Tests for the Error Log page."""

from unittest.mock import patch

from maestro.gui.pages.log_page import LogPage


class TestLogPage:
    def test_load_log_with_content(self, qtbot, tmp_path):
        log_file = tmp_path / "test.log"
        log_file.write_text("2026-03-02 [INFO] Test line\n")
        page = LogPage()
        qtbot.addWidget(page)
        with patch("maestro.gui.pages.log_page.get_log_path", return_value=log_file):
            page.load_log()
        assert "Test line" in page._log_viewer.toPlainText()

    def test_load_log_empty_state(self, qtbot, tmp_path):
        log_file = tmp_path / "nonexistent.log"
        page = LogPage()
        qtbot.addWidget(page)
        with patch("maestro.gui.pages.log_page.get_log_path", return_value=log_file):
            page.load_log()
        assert "No log entries" in page._log_viewer.toPlainText()

    def test_show_event_triggers_load(self, qtbot, tmp_path):
        log_file = tmp_path / "test.log"
        log_file.write_text("Log content here\n")
        page = LogPage()
        qtbot.addWidget(page)
        with patch("maestro.gui.pages.log_page.get_log_path", return_value=log_file):
            page.show()
        assert "Log content" in page._log_viewer.toPlainText()
