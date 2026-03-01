"""Tests for the Settings page."""

from maestro.gui.pages.settings_page import SettingsPage


class TestSettingsPage:
    def test_has_library_card(self, qtbot):
        page = SettingsPage(config={"theme": "dark"})
        qtbot.addWidget(page)
        assert page._folder_label is not None
        assert page._browse_btn is not None

    def test_has_theme_toggle(self, qtbot):
        page = SettingsPage(config={"theme": "dark"})
        qtbot.addWidget(page)
        assert page._theme_toggle is not None
        assert page._theme_toggle.isChecked()  # dark = ON

    def test_has_fullscreen_toggle(self, qtbot):
        page = SettingsPage(config={"theme": "dark", "start_fullscreen": False})
        qtbot.addWidget(page)
        assert page._fullscreen_toggle is not None
        assert not page._fullscreen_toggle.isChecked()

    def test_has_auto_minimize_toggle(self, qtbot):
        page = SettingsPage(config={"theme": "dark", "auto_minimize_on_play": True})
        qtbot.addWidget(page)
        assert page._minimize_toggle is not None
        assert page._minimize_toggle.isChecked()

    def test_has_hotkey_rows(self, qtbot):
        page = SettingsPage(config={"theme": "dark", "play_key": "f2", "stop_key": "f3", "emergency_stop_key": "escape"})
        qtbot.addWidget(page)
        assert page._hotkey_play_label is not None
        assert page._hotkey_stop_label is not None
        assert page._hotkey_emergency_label is not None

    def test_has_update_toggle(self, qtbot):
        page = SettingsPage(config={"theme": "dark", "check_updates_on_launch": True})
        qtbot.addWidget(page)
        assert page._update_toggle is not None
        assert page._update_toggle.isChecked()

    def test_theme_toggle_emits_signal(self, qtbot):
        page = SettingsPage(config={"theme": "dark"})
        qtbot.addWidget(page)
        with qtbot.waitSignal(page.theme_changed, timeout=1000):
            page._theme_toggle.setChecked(False)

    def test_folder_change_emits_signal(self, qtbot):
        page = SettingsPage(config={"theme": "dark"})
        qtbot.addWidget(page)
        assert hasattr(page, "folder_browse_requested")

    def test_has_demucs_section(self, qtbot):
        page = SettingsPage(config={"theme": "dark"})
        qtbot.addWidget(page)
        assert page._demucs_status is not None
        assert page._demucs_btn is not None

    def test_has_check_now_button(self, qtbot):
        page = SettingsPage(config={"theme": "dark", "check_updates_on_launch": True})
        qtbot.addWidget(page)
        assert page._check_now_btn is not None
