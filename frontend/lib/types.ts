/** One row of the Neon `jobs` table, as returned by JOB_COLUMNS in lib/sql.ts. */
export interface Job {
  job_id: string;
  title: string;
  company: string;
  location: string | null;
  work_type: string;
  employment_type: string;
  remote_eligibility: string;
  salary: string | null;
  skills_matched: string[];
  skills_missing: string[];
  match_score: number | null;
  match_tier: string;
  scoring_version: number | null;
  match_breakdown: unknown;
  recommended_action: string | null;
  source: string;
  job_url: string;
  date_posted: string | null; // YYYY-MM-DD
  application_deadline: string | null; // YYYY-MM-DD
  first_seen: string; // ISO UTC
  last_seen: string; // ISO UTC
  is_active: boolean;
  is_repost: boolean;
  description_excerpt: string;
  checklist: string | null;
  application_status: string;
}

export interface ListResult {
  jobs: Job[];
  total: number;
  page: number;
  pages: number;
}

export interface Overview {
  total: number;
  new7d: number;
  tiers: Record<string, number>;
  sources: { source: string; n: number }[];
  publishedAt: string | null;
}

export interface FilterOptions {
  sources: string[];
  statuses: string[];
  workTypes: string[];
  eligibility: string[];
  employmentTypes: string[];
  skills: { skill: string; n: number }[];
}
