"""Tests for the ToggleSwitch custom widget."""

from maestro.gui.toggle_switch import ToggleSwitch


class TestToggleSwitch:
    def test_initial_checked_state(self, qtbot):
        switch = ToggleSwitch(checked=True)
        qtbot.addWidget(switch)
        assert switch.isChecked()

    def test_toggle_changes_state(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        assert not switch.isChecked()
        switch.setChecked(True)
        assert switch.isChecked()
        switch.setChecked(False)
        assert not switch.isChecked()

    def test_toggled_signal_emitted(self, qtbot):
        switch = ToggleSwitch()
        qtbot.addWidget(switch)
        with qtbot.waitSignal(switch.toggled, timeout=1000):
            switch.setChecked(True)
