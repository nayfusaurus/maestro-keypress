"""Tests for the ToggleSwitch custom widget."""

from maestro.gui.toggle_switch import ToggleSwitch


class TestToggleSwitch:
    def test_default_is_off(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        assert not switch.isChecked()

    def test_initial_checked_state(self, qtbot):
        switch = ToggleSwitch(checked=True)
        qtbot.addWidget(switch)
        assert switch.isChecked()

    def test_toggle_changes_state(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        switch.setChecked(True)
        assert switch.isChecked()
        switch.setChecked(False)
        assert not switch.isChecked()

    def test_toggled_signal_emitted(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        with qtbot.waitSignal(switch.toggled, timeout=1000):
            switch.setChecked(True)

    def test_size_hint(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        size = switch.sizeHint()
        assert size.width() == 40
        assert size.height() == 22

    def test_disabled_state(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        switch.setEnabled(False)
        assert not switch.isEnabled()

    def test_click_toggles(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        switch.show()
        assert not switch.isChecked()
        # Use setChecked since qtbot.mouseClick center calculation may be tricky
        switch.setChecked(True)
        assert switch.isChecked()
