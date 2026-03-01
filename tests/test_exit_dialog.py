"""Tests for the exit confirmation dialog."""

from maestro.gui.exit_dialog import ExitDialog


class TestExitDialog:
    def test_dialog_has_title(self, qtbot):
        dialog = ExitDialog()
        qtbot.addWidget(dialog)
        assert dialog.windowTitle() == "Exit Maestro"

    def test_dialog_is_modal(self, qtbot):
        dialog = ExitDialog()
        qtbot.addWidget(dialog)
        assert dialog.isModal()

    def test_dialog_has_cancel_and_exit_buttons(self, qtbot):
        dialog = ExitDialog()
        qtbot.addWidget(dialog)
        assert dialog._cancel_btn is not None
        assert dialog._exit_btn is not None

    def test_dialog_size(self, qtbot):
        dialog = ExitDialog()
        qtbot.addWidget(dialog)
        assert dialog.width() == 320
        assert dialog.height() == 160

    def test_exit_button_is_primary(self, qtbot):
        dialog = ExitDialog()
        qtbot.addWidget(dialog)
        assert dialog._exit_btn.property("class") == "primary"
