"""Tests for the IconRail navigation widget."""

from maestro.gui.icon_rail import IconRail


class TestIconRail:
    def test_rail_has_fixed_width(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        assert rail.fixedWidth() == 80

    def test_rail_emits_page_changed(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        with qtbot.waitSignal(rail.page_changed, timeout=1000):
            rail.set_active(1)

    def test_rail_has_exit_signal(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        assert hasattr(rail, "exit_clicked")

    def test_set_active_updates_index(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        rail.set_active(2)
        assert rail.active_index() == 2

    def test_initial_active_is_zero(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        assert rail.active_index() == 0

    def test_disabled_pages_blocks_activation(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        rail.set_active(1)  # Go to settings first
        assert rail.active_index() == 1
        rail.set_disabled_pages({0, 2, 3})
        rail.set_active(0)  # Try to go to disabled dashboard
        assert rail.active_index() == 1  # Should stay on settings

    def test_notification_badge(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        rail.set_badge(1, True)
        assert 1 in rail._badges
        rail.set_badge(1, False)
        assert 1 not in rail._badges

    def test_page_count(self, qtbot):
        rail = IconRail()
        qtbot.addWidget(rail)
        assert rail.page_count() == 4
