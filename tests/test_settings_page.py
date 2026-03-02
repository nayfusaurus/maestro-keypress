"""Tests for the Settings page."""

from maestro.gui.pages.settings_page import SettingsPage


class TestSettingsPage:
    def test_theme_toggle_emits_signal(self, qtbot):
        page = SettingsPage(config={"theme": "dark"})
        qtbot.addWidget(page)
        with qtbot.waitSignal(page.theme_changed, timeout=1000):
            page._theme_toggle.setChecked(False)

    def test_set_update_status(self, qtbot):
        page = SettingsPage(config={"theme": "dark"})
        qtbot.addWidget(page)
        page.set_update_status("Up to date")
        assert page._update_status.text() == "Up to date"
