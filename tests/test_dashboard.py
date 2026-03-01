"""Tests for the Dashboard page."""

from maestro.gui.pages.dashboard import DashboardPage


class TestDashboardPage:
    def test_speed_snaps_to_tenths(self, qtbot):
        page = DashboardPage(config={"speed": 1.0})
        qtbot.addWidget(page)
        page._speed_slider.setValue(15)
        assert page._speed_label.text() == "1.5x"

    def test_speed_slider_range(self, qtbot):
        page = DashboardPage(config={"speed": 1.0})
        qtbot.addWidget(page)
        assert page._speed_slider.minimum() == 5
        assert page._speed_slider.maximum() == 20
