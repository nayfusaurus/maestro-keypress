"""Tests for the Info page (About + Disclaimer)."""

from maestro.gui.constants import APP_VERSION, DISCLAIMER_TEXT
from maestro.gui.pages.info_page import InfoPage


class TestInfoPage:
    def test_shows_app_version(self, qtbot):
        page = InfoPage()
        qtbot.addWidget(page)
        assert APP_VERSION in page._version_label.text()

    def test_shows_disclaimer_text(self, qtbot):
        page = InfoPage()
        qtbot.addWidget(page)
        assert DISCLAIMER_TEXT[:30] in page._disclaimer_text.toPlainText()

    def test_disclaimer_is_read_only(self, qtbot):
        page = InfoPage()
        qtbot.addWidget(page)
        assert page._disclaimer_text.isReadOnly()

    def test_first_launch_shows_buttons(self, qtbot):
        page = InfoPage(first_launch=True)
        qtbot.addWidget(page)
        page.show()
        assert page._accept_btn.isVisible()
        assert page._reject_btn.isVisible()

    def test_normal_launch_hides_buttons(self, qtbot):
        page = InfoPage(first_launch=False)
        qtbot.addWidget(page)
        page.show()
        assert not page._accept_btn.isVisible()
        assert not page._reject_btn.isVisible()

    def test_accept_emits_signal(self, qtbot):
        page = InfoPage(first_launch=True)
        qtbot.addWidget(page)
        with qtbot.waitSignal(page.disclaimer_accepted, timeout=1000):
            page._accept_btn.click()

    def test_reject_emits_signal(self, qtbot):
        page = InfoPage(first_launch=True)
        qtbot.addWidget(page)
        with qtbot.waitSignal(page.disclaimer_rejected, timeout=1000):
            page._reject_btn.click()

    def test_hide_buttons_after_accept(self, qtbot):
        page = InfoPage(first_launch=True)
        qtbot.addWidget(page)
        page._accept_btn.click()
        assert not page._accept_btn.isVisible()
        assert not page._reject_btn.isVisible()
