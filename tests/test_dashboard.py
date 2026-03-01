"""Tests for the Dashboard page."""

from maestro.gui.pages.dashboard import DashboardPage


class TestDashboardPage:
    def test_has_import_section(self, qtbot):
        page = DashboardPage(config={})
        qtbot.addWidget(page)
        assert page._import_panel is not None

    def test_has_game_combo(self, qtbot):
        page = DashboardPage(config={"game_mode": "Heartopia"})
        qtbot.addWidget(page)
        assert page._game_combo is not None

    def test_has_speed_slider(self, qtbot):
        page = DashboardPage(config={"speed": 1.0})
        qtbot.addWidget(page)
        assert page._speed_slider is not None
        assert page._speed_slider.minimum() == 5
        assert page._speed_slider.maximum() == 20

    def test_speed_snaps_to_tenths(self, qtbot):
        page = DashboardPage(config={"speed": 1.0})
        qtbot.addWidget(page)
        page._speed_slider.setValue(15)
        assert page._speed_label.text() == "1.5x"

    def test_has_song_list(self, qtbot):
        page = DashboardPage(config={})
        qtbot.addWidget(page)
        assert page._song_list is not None

    def test_has_filter_and_refresh(self, qtbot):
        page = DashboardPage(config={})
        qtbot.addWidget(page)
        assert page._search_entry is not None
        assert page._refresh_btn is not None

    def test_has_transport_controls(self, qtbot):
        page = DashboardPage(config={})
        qtbot.addWidget(page)
        assert page._controls is not None
        assert page._now_playing is not None

    def test_has_toggle_switches(self, qtbot):
        page = DashboardPage(config={"transpose": False, "show_preview": False})
        qtbot.addWidget(page)
        assert page._transpose_toggle is not None
        assert page._preview_toggle is not None

    def test_left_column_width(self, qtbot):
        page = DashboardPage(config={})
        qtbot.addWidget(page)
        assert page._left_scroll.maximumWidth() == 400
        assert page._left_scroll.minimumWidth() == 400
