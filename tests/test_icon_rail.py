"""Tests for the IconRail navigation widget."""

from maestro.gui.icon_rail import IconRail


class TestIconRail:
    def test_rail_emits_page_changed(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        with qtbot.waitSignal(rail.page_changed, timeout=1000):
            rail.set_active(1)

    def test_set_active_updates_index(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        rail.set_active(2)
        assert rail.active_index() == 2

    def test_disabled_pages_blocks_activation(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        rail.set_active(1)
        assert rail.active_index() == 1
        rail.set_disabled_pages({0, 2, 3})
        rail.set_active(0)
        assert rail.active_index() == 1  # stays on settings

    def test_notification_badge(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        rail.set_badge(1, True)
        assert 1 in rail._badges
        rail.set_badge(1, False)
        assert 1 not in rail._badges
