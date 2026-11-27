// SPDX-License-Identifier: MPL-2.0
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {DatabaseSync} from "node:sqlite";
import test from "node:test";
import worker from "./worker.mjs";

test("validates, deduplicates daily country counts, ignores stale revisions and expires data", async () => {
  const db = new DatabaseSync(":memory:");
  db.exec(readFileSync(new URL("./schema.sql", import.meta.url), "utf8"));
  const env = {
    LIMITER: {limit: async () => ({success: true})},
    DB: {
      prepare: sql => ({
        bind: (...args) => () => db.prepare(sql).run(...args),
        run: () => db.prepare(sql).run(),
      }),
      batch: statements => statements.map(s => typeof s === "function" ? s() : s.run()),
    },
  };
  const report = {schema: 1, day: new Date().toISOString().slice(0,10), version: "2.1.0",
    installation: "25032444-a413-436a-b389-175f0ab148d7", revision: 2,
    device: {windows: "11/26100", language: "en-US", width: 5, height: 3},
    groups: {"HEARTOPIA/KEYS_22": {attempt: 2, started: 1}}};
  async function send(body, country = "SG") {
    const request = new Request("https://local.test/report", {
      method: "POST", headers: {"content-type": "application/json"}, body: JSON.stringify(body),
    });
    request.cf = {country};
    return (await worker.fetch(request, env)).status;
  }
  assert.equal(await send({...report, song: "private.mid"}), 400);
  assert.equal(await send({...report, groups: {"HEARTOPIA/KEYS_22": {file: "private.mid"}}}), 400);
  assert.equal(await send(report), 204);
  assert.equal(await send(report), 204);
  assert.equal(await send({...report, revision: 1, groups: {}}, "US"), 204);
  assert.equal(db.prepare("SELECT revision FROM daily").get().revision, 2);
  assert.equal(db.prepare("SELECT sum(installs) AS n FROM countries").get().n, 1);
  assert.equal(db.prepare("SELECT country FROM countries").get().country, "SG");
  db.exec("UPDATE daily SET day=date('now','-90 days'); UPDATE countries SET day=date('now','-90 days')");
  await worker.scheduled({}, env);
  assert.equal(db.prepare("SELECT count(*) AS n FROM daily").get().n, 0);
  assert.equal(db.prepare("SELECT count(*) AS n FROM countries").get().n, 0);
  db.close();
});
