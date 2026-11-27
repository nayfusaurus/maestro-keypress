# Maestro usage reporting

The desktop client sends daily snapshots to the Worker's public `POST /report` route.
Only the Worker accesses D1. Read reports privately in the D1 dashboard. No account token
belongs in the desktop app or GitHub repository.

## Deploy to your Cloudflare account

Use a current Node.js LTS installation and run these commands from this directory.

1. Sign in and create the database.

   ```sh
   npx wrangler@4 login
   npx wrangler@4 d1 create maestro-metrics
   ```

2. Copy `wrangler.example.toml` to `wrangler.toml`. Replace
   `REPLACE_WITH_D1_DATABASE_ID` with the UUID printed above. Keep the binding names
   `DB` and `LIMITER`. Use an unused rate-limiter namespace ID if your account already
   uses 1001. The local configuration file is ignored by Git.

3. Create the tables, then deploy.

   ```sh
   npx wrangler@4 d1 execute maestro-metrics --remote --file=schema.sql
   npx wrangler@4 deploy
   ```

   Select a workers.dev subdomain if Cloudflare prompts you. The configuration installs
   a daily 00:05 UTC retention job and disables Worker observability. Review account-level
   log exports separately. The database retains 90 UTC days of snapshots.

4. In GitHub → repository Settings → Secrets and variables → Actions → Variables,
   create **MAESTRO_METRICS_URL** with the deployed HTTPS address followed by `/report`.
   The Windows build embeds this public URL. Configure it **before building the release**.
   For local source runs or local executable builds, set the environment variable of the
   same name. With no URL the app makes no reporting requests.

5. Smoke-test using a staging Worker and a separate D1 database first (change the Worker
   and database names in the local config). Launch Maestro with its URL, accept the terms
   and enable sharing. Open the D1 console and run:

   ```sql
   SELECT day, version, count(*) AS reporting_installations
   FROM daily GROUP BY day, version ORDER BY day DESC;
   SELECT day, country, installs FROM countries ORDER BY day DESC;
   ```

   Confirm an unchecked first launch creates no usage database or new server row.
   Test disabling sharing, restarting, and playback offline. Switching sharing off deletes
   the local queue and identifier; an upload already in transit can still reach the endpoint.
   Replace the staging URL with the production URL before building the public executable.

## Reading the data

The uploader retries dirty snapshots at startup and every 15 minutes while Maestro runs.
Offline snapshots remain local for up to seven previous UTC days. An installation can
appear under more than one version per day. Country totals count the first upload for each
installation/activity day; country reflects the connection at upload. You cannot join a
country to an installation. Width and height are bucket numbers in 200 logical pixels.
For example, width 5 means 1000–1199. A value of 50 means 10000 or more.

Run the SQL in `queries.sql` in the private D1 console. Cohorts use the earliest day
visible in the retention window, so returning installations after a long absence may
appear new. Limit conclusions to installations that shared data. An installation ID
does not verify identity, and public clients can submit fabricated reports.

[Cloudflare D1 setup](https://developers.cloudflare.com/d1/get-started/) ·
[Worker rate limiting](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/) ·
[Scheduled cleanup](https://developers.cloudflare.com/workers/configuration/cron-triggers/)
