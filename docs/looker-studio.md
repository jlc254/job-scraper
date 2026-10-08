# Looker Studio dashboard

Looker Studio is the free Google tool that turns a Sheet into charts. Google's current documentation
calls it **Data Studio**; it is the same product (datastudio.google.com / lookerstudio.google.com).

You build the report once in the browser, no code. The job scraper keeps the data fresh.

## How the data gets there

Looker Studio reads one worksheet per data source, and wants one type per column and a single header
row. The raw `Jobs` tab does not fit that (text timestamps, a JSON column, skills joined with `;`). So
every run rebuilds six tidy tabs in the same Sheet, and you connect Looker Studio to those:

| Tab | One row per | Use it for |
|---|---|---|
| `Dash_Jobs` | job | Everything about jobs, scores, your application status |
| `Dash_Skills` | job and skill | What skills jobs ask for, and which ones you lack |
| `Dash_Sources` | source and run | Source health: found/new counts, failures |
| `Dash_Runs` | run | Run duration and totals |
| `Dash_Excluded` | filtered-out job | Why jobs are being excluded |
| `Dash_Meta` | (one row) | "Data refreshed at" |

**Do not edit these tabs.** They are overwritten on every run. Keep your own notes and charts elsewhere.
Private columns (`notes`, `description_excerpt`, `all_urls`) are never copied into them.

Refresh them any time without fetching anything: Actions tab, daily-run, Run workflow, mode `dashboard`
(or `python main.py dashboard` on your machine). Create them for the first time the same way, or just wait for the next run.

## Step 1: create one data source per tab

For each of the six tabs: Looker Studio home, **Create**, **Data source**, **Google Sheets**, pick the
spreadsheet and the `Dash_...` worksheet. Keep **Use first row as headers** ticked, then **Connect**.

Set **Data credentials** to **Owner's credentials**. Viewers then need no access to the Sheet, and all of them
share one freshness setting. Do not share the report with anyone you would not show your application history.

Data freshness for Sheets is every 15 minutes by default (options: 15 minutes, 1, 4 or 12 hours). The scraper
only writes twice a day, so 4 hours is plenty. Editors can press **More options, Refresh data** at any time.

## Step 2: check the field types

In each data source's field list, date fields need the calendar icon, not `123` or `ABC`:

- `Dash_Jobs`: `first_seen`, `posted`, `deadline`, `applied_on`, `follow_up_due`
- `Dash_Skills`: `first_seen`. `Dash_Sources` / `Dash_Runs`: `run_date`, `run_time`. `Dash_Excluded`: `excluded_on`. `Dash_Meta`: `refreshed_at`

The scraper writes them as real Sheets dates and formats the columns as dates, which is what Google asks for.
If one still shows as a number, set its **Type** to Date (or Date & Time for `run_time` and `refreshed_at`) in the data
source, then click **Refresh fields**. Booleans (`is_active`, `notified`, `is_repost`, `healthy`) should show as Boolean.

Whenever a column is added or renamed later (a new version of this tool), open the data source and **Refresh fields**.
Google does not pick up changed columns by itself.

## Step 3: calculated fields (in the `Dash_Jobs` data source)

Add these with **Add a field**. If a formula is rejected, check the argument order on Google's function reference for that function.

| Name | Formula |
|---|---|
| Job Link | `HYPERLINK(url, title)` |
| Open Top/Strong | `COUNT_DISTINCT(CASE WHEN (tier = "top" OR tier = "strong") AND status = "New" THEN job_id END)` |
| Applied | `COUNT_DISTINCT(CASE WHEN status = "Applied" THEN job_id END)` |
| Acted On | `COUNT_DISTINCT(CASE WHEN status = "Applied" OR status = "Interview" OR status = "Offer" OR status = "Rejected" THEN job_id END)` |
| Acted-On Share | `Acted On / COUNT_DISTINCT(job_id)` (format as percent) |
| Follow-ups Due | `COUNT_DISTINCT(CASE WHEN follow_up_due <= TODAY() THEN job_id END)` |
| Days to Deadline | `DATE_DIFF(deadline, TODAY())` |

## Step 4: build the pages

Add each chart from the matching data source. Controls (date range, drop-downs) only filter charts that use the
same data source, so put a control on each page for the source its charts use.

**Page 1: Today** (`Dash_Jobs`)
- Scorecards: `Open Top/Strong`, `Follow-ups Due`, and record count with a *last 7 days* date range on `first_seen` ("new this week").
- Table, sorted by `score` descending: `Job Link`, `company`, `score`, `tier`, `deadline`, `remote_eligibility`.
  Filter: `status` = New, `tier` is top or strong, `is_active` = true.
- `Dash_Meta`: a scorecard on `refreshed_at`, so you can see how stale the page is.

**Page 2: Pipeline** (`Dash_Jobs`)
- Bar chart: record count by `status`.
- Time series: `Applied` by `applied_on`.
- Table of follow-ups: `Job Link`, `company`, `applied_on`, `follow_up_due`, sorted by `follow_up_due`. Filter: `status` = Applied.

**Page 3: Market** (`Dash_Jobs`, `Dash_Excluded`)
- Stacked column: record count by week of `first_seen`, broken down by `tier`.
- Bar: record count by `source`. Pie: record count by `remote_eligibility`.
- Table: top `company` by record count, filtered to Top and Strong.
- `Dash_Excluded`: bar of record count by `reason`, broken down by `source` (why jobs are being thrown out).

**Page 4: Skills** (`Dash_Skills`)
- Bar: count of `job_id` by `skill`, filtered to `match` = missing and `tier` top or strong. This is your learning list.
- Stacked bar: most requested `skill`, broken down by `match`.
- Pivot table: `skill` by `importance`, metric record count.

**Page 5: Source health** (`Dash_Sources`, `Dash_Runs`)
- Time series: `found` by `run_date`, one line per `source`. A line dropping to zero is the signal to investigate.
- Table: `run_time`, `source`, `status`, `found`, `new`, `error`, newest first, with conditional formatting on `status` not equal to `ok`.
- `Dash_Runs`: time series of `duration_s` by `run_date`.

**Page 6: Is the scoring right?** (`Dash_Jobs`)
- Bar: average of `title_pts`, `skills_pts`, `location_pts`, `experience_pts`, `salary_pts`, `freshness_pts`, `industry_pts`, by `tier`.
- Pivot: rows `tier`, columns `status`, metric record count. Top and Strong jobs you never act on mean the scoring needs adjusting
  in `scoring.yaml`; Weak or Potential jobs you apply to mean it is too strict. Bump `scoring_version` when you change it, and use
  `scoring_version` as a filter to compare before and after.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Can't find worksheet" or empty chart | Run the `dashboard` mode in Actions once, then refresh the data source |
| A date shows as a number | Set the field Type to Date in the data source, then Refresh fields |
| Newly added column is missing | Open the data source and click Refresh fields |
| Numbers look stale | Press More options, Refresh data, or lower the data freshness setting |
| Charts empty after the Sheet was shared with someone else | Data credentials must be Owner's credentials |
| Source health shows no rows | `Dash_Sources` fills from the first run that saves to the Sheet |
