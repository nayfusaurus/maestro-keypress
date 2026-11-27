-- SPDX-License-Identifier: MPL-2.0
CREATE TABLE IF NOT EXISTS daily (
    installation TEXT NOT NULL, day TEXT NOT NULL, version TEXT NOT NULL,
    revision INTEGER NOT NULL, device TEXT NOT NULL, groups_json TEXT NOT NULL,
    PRIMARY KEY (installation, day, version)
);
CREATE INDEX IF NOT EXISTS daily_day ON daily(day);
CREATE TABLE IF NOT EXISTS countries (
    day TEXT NOT NULL, country TEXT NOT NULL, installs INTEGER NOT NULL,
    PRIMARY KEY (day, country)
);
