# SPDX-License-Identifier: MPL-2.0
import sqlite3
from unittest.mock import Mock

import requests

from maestro.gui.privacy import WelcomeDialog, review_choices
from maestro.metrics import UsageMetrics


def test_welcome_requires_terms_but_sharing_is_optional(qtbot):
    dialog = WelcomeDialog()
    qtbot.addWidget(dialog)
    assert not dialog.proceed.isEnabled()
    assert dialog.sharing.isChecked()
    dialog.sharing.setChecked(False)
    dialog.terms.setChecked(True)
    dialog.proceed.click()
    assert dialog.result() == dialog.DialogCode.Accepted
    assert not dialog.sharing.isChecked()


def test_offline_retry_and_opt_out(tmp_path, monkeypatch):
    post = Mock(side_effect=requests.ConnectionError)
    monkeypatch.setattr("maestro.metrics.requests.post", post)
    store = UsageMetrics(tmp_path, "https://metrics.example/report")
    store.configure(False)
    store.record()
    store.flush()
    assert not store.path.exists()
    post.assert_not_called()

    store.configure(True)
    store.context = {"windows": "11/26100", "language": "en-US", "width": 5, "height": 3}
    store.record()
    store._send(store.generation)
    baseline = post.call_args.kwargs["json"]
    assert baseline["groups"] == {}
    store.record("HEARTOPIA", "KEYS_22", ("attempt", "started"))
    post.side_effect = None
    post.return_value.status_code = 204
    store._send(store.generation)
    report = post.call_args.kwargs["json"]
    assert report["installation"] == baseline["installation"]
    assert report["revision"] > baseline["revision"]
    assert report["groups"] == {"HEARTOPIA/KEYS_22": {"attempt": 1, "started": 1}}
    assert set(report) == {
        "schema",
        "installation",
        "day",
        "version",
        "revision",
        "device",
        "groups",
    }
    post.reset_mock()
    store._send(store.generation)
    post.assert_not_called()

    old_generation = store.generation
    store.configure(False)
    store.record("HEARTOPIA", "KEYS_22", ("completed",), generation=old_generation)
    store.flush()
    assert not store.path.exists()
    store.configure(True)
    with sqlite3.connect(store.path) as db:
        assert db.execute("SELECT id FROM identity").fetchone()[0] != report["installation"]
        assert db.execute("SELECT count(*) FROM daily").fetchone()[0] == 0


def test_upgrade_cancel_accept_without_sharing_and_restart(monkeypatch):
    dialog = Mock()
    factory = Mock(return_value=dialog)
    monkeypatch.setattr("maestro.gui.privacy.WelcomeDialog", factory)
    config = {"disclaimer_accepted": True}
    dialog.exec.return_value = 0
    assert not review_choices(config)
    assert config == {"disclaimer_accepted": True}
    dialog.exec.return_value = 1
    dialog.sharing.isChecked.return_value = False
    assert review_choices(config)
    assert config["share_usage"] is False
    assert review_choices(config.copy())
    assert factory.call_count == 2
