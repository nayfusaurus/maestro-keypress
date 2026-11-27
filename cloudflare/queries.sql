-- SPDX-License-Identifier: MPL-2.0
-- Active installations by version during the last 30 UTC days.
SELECT version, count(DISTINCT installation) AS active_installations
FROM daily WHERE day >= date('now','-29 days') GROUP BY version;

-- Playback attempts and sessions with input failures by version and layout.
SELECT version, g.key AS game_layout,
       sum(coalesce(json_extract(g.value,'$.attempt'),0)) AS attempts,
       sum(coalesce(json_extract(g.value,'$.input_failure'),0)) AS failures
FROM daily, json_each(groups_json) AS g GROUP BY version, g.key;

-- Seven-day activation and return rates for cohorts with complete observation.
WITH days AS (
  SELECT installation, day,
         max(EXISTS (SELECT 1 FROM json_each(groups_json) AS g
                     WHERE json_extract(g.value,'$.started') > 0)) AS played
  FROM daily GROUP BY installation, day
), cohorts AS (
  SELECT installation, min(day) AS first_seen,
         min(CASE WHEN played THEN day END) AS first_play
  FROM days GROUP BY installation
)
SELECT
  avg(CASE WHEN first_seen <= date('now','-7 days')
           THEN CASE WHEN first_play < date(first_seen,'+7 days') THEN 1.0 ELSE 0 END END)
    AS seven_day_activation,
  avg(CASE WHEN first_play <= date('now','-8 days')
           THEN EXISTS (SELECT 1 FROM days d WHERE d.installation=c.installation
                        AND played AND day > first_play AND day <= date(first_play,'+7 days')) END)
    AS seven_day_return
FROM cohorts AS c;
