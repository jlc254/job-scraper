import { unstable_cache } from "next/cache";
import { Filters, PAGE_SIZE } from "./filters";
import { query } from "./db";
import { JOB_COLUMNS, buildListQuery } from "./sql";
import type { FilterOptions, Job, ListResult, Overview } from "./types";

export async function listJobs(filters: Filters): Promise<ListResult> {
  const q = buildListQuery(filters);
  const [jobs, counts] = await Promise.all([
    query<Job>(q.text, q.params),
    query<{ total: number }>(q.countText, q.countParams),
  ]);
  const total = counts[0]?.total ?? 0;
  return { jobs, total, page: filters.page, pages: Math.max(1, Math.ceil(total / PAGE_SIZE)) };
}

export async function getJob(id: string): Promise<Job | null> {
  const rows = await query<Job>(`SELECT ${JOB_COLUMNS} FROM jobs WHERE job_id = $1`, [id]);
  return rows[0] ?? null;
}

async function loadOverview(): Promise<Overview> {
  const [stats, sources] = await Promise.all([
    query<{
      total: number;
      new7d: number;
      top: number;
      strong: number;
      potential: number;
      weak: number;
      published_at: string | null;
    }>(`
      SELECT
        count(*)::int AS total,
        (count(*) FILTER (WHERE first_seen >= now() - interval '7 days'))::int AS new7d,
        (count(*) FILTER (WHERE match_tier = 'top'))::int AS top,
        (count(*) FILTER (WHERE match_tier = 'strong'))::int AS strong,
        (count(*) FILTER (WHERE match_tier = 'potential'))::int AS potential,
        (count(*) FILTER (WHERE match_tier = 'weak'))::int AS weak,
        (SELECT to_char(published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
           FROM publish_meta WHERE id = 1) AS published_at
      FROM jobs`),
    query<{ source: string; n: number }>(
      `SELECT source, count(*)::int AS n FROM jobs GROUP BY source ORDER BY n DESC, source`,
    ),
  ]);
  const s = stats[0];
  return {
    total: s?.total ?? 0,
    new7d: s?.new7d ?? 0,
    tiers: { top: s?.top ?? 0, strong: s?.strong ?? 0, potential: s?.potential ?? 0, weak: s?.weak ?? 0 },
    sources,
    publishedAt: s?.published_at ?? null,
  };
}

async function loadFilterOptions(): Promise<FilterOptions> {
  const [kinds, skills] = await Promise.all([
    query<{ kind: string; value: string | null }>(`
      SELECT 'source' AS kind, source AS value FROM jobs GROUP BY source
      UNION ALL SELECT 'status', application_status FROM jobs GROUP BY application_status
      UNION ALL SELECT 'work_type', work_type FROM jobs GROUP BY work_type
      UNION ALL SELECT 'eligibility', remote_eligibility FROM jobs GROUP BY remote_eligibility
      UNION ALL SELECT 'employment_type', employment_type FROM jobs GROUP BY employment_type`),
    query<{ skill: string; n: number }>(`
      SELECT s AS skill, count(*)::int AS n FROM jobs, unnest(skills_matched) AS s
      GROUP BY s ORDER BY n DESC, s LIMIT 40`),
  ]);
  const pick = (kind: string) =>
    kinds
      .filter((r) => r.kind === kind && r.value)
      .map((r) => r.value as string)
      .sort((a, b) => a.localeCompare(b));
  return {
    sources: pick("source"),
    statuses: pick("status"),
    workTypes: pick("work_type"),
    eligibility: pick("eligibility"),
    employmentTypes: pick("employment_type"),
    skills,
  };
}

// Short cache spares free-tier compute. Both values only change when `publish` runs.
export const overview = unstable_cache(loadOverview, ["overview"], { revalidate: 60 });
export const filterOptions = unstable_cache(loadFilterOptions, ["filter-options"], { revalidate: 60 });
