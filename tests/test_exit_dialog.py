"""Tests for the exit confirmation dialog."""

from maestro.gui.exit_dialog import ExitDialog


class TestExitDialog:
    def test_dialog_is_modal(self, qtbot):
        dialog = ExitDialog()
        qtbot.addWidget(dialog)
        assert dialog.isModal()
