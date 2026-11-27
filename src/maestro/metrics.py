# SPDX-License-Identifier: MPL-2.0
"""Daily usage snapshots. Only open this store after the user enables sharing."""

import json
import locale
import os
import sqlite3
import sys
import threading
import uuid
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import requests

from maestro.gui.constants import APP_VERSION


def endpoint() -> str:
    url = os.getenv("MAESTRO_METRICS_URL", "").strip()
    bundled = Path(__file__).with_name("metrics_endpoint.txt")
    if not url and bundled.is_file():
        url = bundled.read_text(encoding="utf-8-sig").strip()
    return url if url.startswith("https://") and url.endswith("/report") else ""


def environment(width: int, height: int) -> dict:
    windows = language = "unknown"
    if sys.platform == "win32":
        import ctypes

        build = sys.getwindowsversion().build
        windows = f"{'11' if build >= 22000 else '10' if build >= 10240 else 'older'}/{build}"
        lang_id = ctypes.windll.user32.GetKeyboardLayout(0) & 0xFFFF
        language = locale.windows_locale.get(lang_id, "unknown").replace("_", "-")
    # Logical pixel ranges, in increments of 200. Never inspect other windows.
    return {
        "windows": windows,
        "language": language,
        "width": min(width // 200, 50),
        "height": min(height // 200, 50),
    }


class UsageMetrics:
    def __init__(self, directory: Path, url: str):
        self.path = directory / "usage.sqlite"
        self.url = url
        self.enabled = False
        self.lock = threading.RLock()
        self.upload: threading.Thread | None = None
        self.context: dict = {}
        self.generation = 0

    def configure(self, enabled: bool) -> None:
        with self.lock:
            self.generation += 1
            self.enabled = enabled
            if not enabled:
                self.context = {}
                self.path.unlink(missing_ok=True)
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(self.path)) as db, db:
                db.execute("CREATE TABLE IF NOT EXISTS identity (slot INTEGER PRIMARY KEY,id TEXT)")
                db.execute("INSERT OR IGNORE INTO identity VALUES (1,?)", (str(uuid.uuid4()),))
                db.execute("""CREATE TABLE IF NOT EXISTS daily (
                    day TEXT, version TEXT, revision INTEGER, sent INTEGER, payload TEXT,
                    PRIMARY KEY(day,version))""")

    def record(
        self,
        game: str = "",
        layout: str = "",
        counters: tuple[str, ...] = (),
        *,
        generation: int | None = None,
    ) -> None:
        with self.lock:
            if not self.enabled or (generation is not None and generation != self.generation):
                return
            day = datetime.now(UTC).date().isoformat()
            try:
                with closing(sqlite3.connect(self.path, isolation_level="IMMEDIATE")) as db, db:
                    db.execute("DELETE FROM daily WHERE day < date('now','-7 days')")
                    row = db.execute(
                        "SELECT payload FROM daily WHERE day=? AND version=?", (day, APP_VERSION)
                    ).fetchone()
                    payload = json.loads(row[0]) if row else {"groups": {}}
                    changed = payload.get("device") != self.context
                    if not counters and not changed:
                        return
                    payload["device"] = self.context
                    if counters:
                        group = payload["groups"].setdefault(f"{game}/{layout}", {})
                        for name in counters:
                            group[name] = min(100000, group.get(name, 0) + 1)
                    db.execute(
                        """INSERT INTO daily VALUES (?,?,1,0,?)
                        ON CONFLICT(day,version) DO UPDATE SET revision=revision+1,payload=excluded.payload""",
                        (day, APP_VERSION, json.dumps(payload)),
                    )
            except (sqlite3.Error, OSError):
                return  # Telemetry storage must never interrupt playback.

    def flush(self) -> None:
        with self.lock:
            if not self.enabled or not self.url or (self.upload and self.upload.is_alive()):
                return
            self.upload = threading.Thread(target=self._send, args=(self.generation,), daemon=True)
            self.upload.start()

    def _send(self, generation: int) -> None:
        try:
            with self.lock:
                if not self.enabled or self.generation != generation:
                    return
                with closing(sqlite3.connect(self.path)) as db:
                    iid = db.execute("SELECT id FROM identity").fetchone()[0]
                    rows = db.execute("""SELECT day,version,revision,payload FROM daily
                        WHERE revision>sent ORDER BY day LIMIT 16""").fetchall()
            for day, version, revision, raw in rows:
                with self.lock:
                    if not self.enabled or self.generation != generation:
                        return
                body = {
                    "schema": 1,
                    "installation": iid,
                    "day": day,
                    "version": version,
                    "revision": revision,
                    **json.loads(raw),
                }
                response = requests.post(
                    self.url,
                    json=body,
                    timeout=(2, 3),
                    allow_redirects=False,
                    headers={"User-Agent": f"Maestro/{APP_VERSION}"},
                )
                if response.status_code != 204:
                    return
                with self.lock:
                    if not self.enabled or self.generation != generation:
                        return
                    with closing(sqlite3.connect(self.path)) as db, db:
                        db.execute(
                            "UPDATE daily SET sent=? WHERE day=? AND version=?",
                            (revision, day, version),
                        )
        except (requests.RequestException, sqlite3.Error, OSError):
            return  # Retry on the next timer or launch.
