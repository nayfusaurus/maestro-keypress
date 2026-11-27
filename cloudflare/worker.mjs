// SPDX-License-Identifier: MPL-2.0
const layouts = new Set(["HEARTOPIA/KEYS_22", "HEARTOPIA/KEYS_15_DOUBLE", "HEARTOPIA/KEYS_15_TRIPLE",
  "HEARTOPIA/DRUMS", "HEARTOPIA/XYLOPHONE", "WHERE_WINDS_MEET/KEYS_36",
  "WHERE_WINDS_MEET/KEYS_21", "ONCE_HUMAN/DEFAULT"]);
const counters = new Set(["attempt", "started", "completed", "stopped", "input_failure", "unreadable", "zero"]);
const object = value => value !== null && typeof value === "object" && !Array.isArray(value);
const exact = (value, keys) => object(value) && Object.keys(value).length === keys.length
  && keys.every(key => Object.hasOwn(value, key));
const integer = (value, max) => Number.isSafeInteger(value) && value >= 0 && value <= max;
const matches = (value, pattern) => typeof value === "string" && pattern.test(value);

export function valid(report, today = Date.now()) {
  if (!exact(report, ["schema", "installation", "day", "version", "revision", "device", "groups"])) return false;
  const {schema, installation, day, version, revision, device, groups} = report;
  if (schema !== 1 || !matches(installation, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/)
      || !matches(version, /^\d{1,3}\.\d{1,3}\.\d{1,3}$/) || !integer(revision, 2147483647) || !revision
      || !matches(day, /^\d{4}-\d{2}-\d{2}$/)) return false;
  const stamp = Date.parse(day);
  if (!Number.isFinite(stamp) || new Date(stamp).toISOString().slice(0,10) !== day ||
      stamp < today - 9 * 86400000 || stamp > today + 86400000) return false;
  if (!exact(device, ["windows", "language", "width", "height"]) ||
      !matches(device.windows, /^(unknown|(older|10|11)\/\d{1,6})$/) ||
      !matches(device.language, /^(unknown|[a-z]{2,3}(-[A-Za-z0-9]{2,8}){0,2})$/) ||
      !integer(device.width, 50) || !integer(device.height, 50) || !object(groups)) return false;
  return Object.entries(groups).every(([layout, counts]) => layouts.has(layout) && object(counts)
    && Object.entries(counts).every(([name, value]) => counters.has(name) && integer(value, 100000)));
}

export default {
  async fetch(request, env) {
    if (new URL(request.url).pathname !== "/report") return new Response(null, {status: 404});
    if (request.method !== "POST") return new Response(null, {status: 405});
    if (!request.headers.get("content-type")?.startsWith("application/json")) return new Response(null, {status: 415});
    if (!(await env.LIMITER.limit({key: request.headers.get("CF-Connecting-IP") || "unknown"})).success)
      return new Response(null, {status: 429});
    const reader = request.body?.getReader();
    if (!reader) return new Response(null, {status: 400});
    const buffer = new Uint8Array(8192);
    let size = 0;
    for (;;) {
      const {value, done} = await reader.read();
      if (done) break;
      if (size + value.length > buffer.length) {
        await reader.cancel();
        return new Response(null, {status: 413});
      }
      buffer.set(value, size);
      size += value.length;
    }
    let report;
    try { report = JSON.parse(new TextDecoder().decode(buffer.subarray(0, size))); }
    catch { return new Response(null, {status: 400}); }
    if (!valid(report)) return new Response(null, {status: 400});
    const {installation, day, version, revision, device, groups} = report;
    const country = /^[A-Z]{2}$/.test(request.cf?.country ?? "") ? request.cf.country : "XX";
    // The atomic batch counts a country only on the first upload for this installation/day.
    await env.DB.batch([
      env.DB.prepare(`INSERT INTO countries(day,country,installs)
        SELECT ?,?,1 WHERE NOT EXISTS (SELECT 1 FROM daily WHERE installation=? AND day=?)
        ON CONFLICT(day,country) DO UPDATE SET installs=installs+1`).bind(day,country,installation,day),
      env.DB.prepare(`INSERT INTO daily VALUES (?,?,?,?,?,?)
        ON CONFLICT(installation,day,version) DO UPDATE SET revision=excluded.revision,
        device=excluded.device,groups_json=excluded.groups_json WHERE excluded.revision>daily.revision`)
        .bind(installation,day,version,revision,JSON.stringify(device),JSON.stringify(groups)),
    ]);
    return new Response(null, {status: 204});
  },
  async scheduled(controller, env) {
    await env.DB.batch(["daily", "countries"].map(table =>
      env.DB.prepare(`DELETE FROM ${table} WHERE day <= date('now','-90 days')`)));
  },
};
