import { Filters, PAGE_SIZE, clampLimit } from "./filters";

/** Explicit column list. Dates and timestamps are formatted in SQL so the driver never guesses time zones. */
export const JOB_COLUMNS = `
  job_id, title, company, location, work_type, employment_type, remote_eligibility, salary,
  skills_matched, skills_missing, match_score::float8 AS match_score, match_tier, scoring_version,
  match_breakdown, recommended_action, source, job_url,
  to_char(date_posted, 'YYYY-MM-DD') AS date_posted,
  to_char(application_deadline, 'YYYY-MM-DD') AS application_deadline,
  to_char(first_seen AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS first_seen,
  to_char(last_seen AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS last_seen,
  is_active, is_repost, description_excerpt, checklist, application_status`;

/** Sort allowlist. The ORDER BY text never comes from user input. Columns are table-qualified so
 *  they refer to the real columns and not the formatted output aliases. */
export const ORDER_BY = {
  score: "jobs.match_score DESC NULLS LAST, jobs.first_seen DESC, jobs.job_id",
  newest: "jobs.first_seen DESC, jobs.job_id",
  oldest: "jobs.first_seen ASC, jobs.job_id",
  deadline:
    "jobs.application_deadline ASC NULLS LAST, jobs.match_score DESC NULLS LAST, jobs.job_id",
} as const;

export interface ListQuery {
  text: string;
  params: unknown[];
  countText: string;
  countParams: unknown[];
}

/** Builds the list and count queries. Every user value is a bound parameter. */
export function buildListQuery(f: Filters, limit: number = PAGE_SIZE): ListQuery {
  const params: unknown[] = [];
  const where: string[] = [];
  const add = (v: unknown): string => {
    params.push(v);
    return `$${params.length}`;
  };

  where.push(`match_tier = ANY(${add(f.tiers)}::text[])`);
  if (f.q) where.push(`search @@ websearch_to_tsquery('english', ${add(f.q)})`);
  if (f.minScore > 0) where.push(`match_score >= ${add(f.minScore)}`);
  if (f.source) where.push(`source = ${add(f.source)}`);
  if (f.workType) where.push(`work_type = ${add(f.workType)}`);
  if (f.eligibility) where.push(`remote_eligibility = ${add(f.eligibility)}`);
  if (f.employmentType) where.push(`employment_type = ${add(f.employmentType)}`);
  if (f.status) where.push(`application_status = ${add(f.status)}`);
  if (f.foundDays) where.push(`first_seen >= now() - (${add(f.foundDays)}::int * interval '1 day')`);
  if (f.skill) where.push(`skills_matched @> ARRAY[${add(f.skill)}]::text[]`);

  const whereSql = where.length ? `WHERE ${where.join(" AND ")}` : "";
  const countParams = [...params];
  const lim = clampLimit(limit);
  const limitRef = add(lim);
  const offsetRef = add((f.page - 1) * lim);

  return {
    text: `SELECT ${JOB_COLUMNS} FROM jobs ${whereSql} ORDER BY ${ORDER_BY[f.sort]} LIMIT ${limitRef} OFFSET ${offsetRef}`,
    params,
    countText: `SELECT count(*)::int AS total FROM jobs ${whereSql}`,
    countParams,
  };
}
