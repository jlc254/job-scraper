-- 001_init.sql
-- Read-only copy of the dashboard columns (doc 13). The Google Sheet stays the source of truth.
-- Run as the project owner role on the DIRECT (non-pooled) connection string.
-- Idempotent: safe to rerun.

CREATE TABLE IF NOT EXISTS jobs (
  job_id               text PRIMARY KEY,
  title                text NOT NULL,
  company              text NOT NULL,
  location             text,
  work_type            text NOT NULL DEFAULT 'unknown',
  employment_type      text NOT NULL DEFAULT 'unknown',
  remote_eligibility   text NOT NULL DEFAULT 'unclear',
  salary               text,
  skills_matched       text[] NOT NULL DEFAULT '{}',
  skills_missing       text[] NOT NULL DEFAULT '{}',
  match_score          numeric(4,1),
  match_tier           text NOT NULL DEFAULT 'unscored'
                         CHECK (match_tier IN ('top','strong','potential','weak','unscored')),
  scoring_version      integer,
  match_breakdown      jsonb,
  recommended_action   text,
  source               text NOT NULL,
  job_url              text NOT NULL CHECK (job_url ~* '^https?://'),
  date_posted          date,
  application_deadline date,
  first_seen           timestamptz NOT NULL,
  last_seen            timestamptz NOT NULL,
  is_active            boolean NOT NULL DEFAULT true,
  is_repost            boolean NOT NULL DEFAULT false,
  description_excerpt  text NOT NULL DEFAULT '',
  checklist            text,
  application_status   text NOT NULL DEFAULT 'New',
  published_at         timestamptz NOT NULL,
  search tsvector GENERATED ALWAYS AS (
    to_tsvector('english', title || ' ' || company || ' ' || description_excerpt)
  ) STORED
);

CREATE INDEX IF NOT EXISTS jobs_score_idx      ON jobs (match_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS jobs_tier_score_idx ON jobs (match_tier, match_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS jobs_first_seen_idx ON jobs (first_seen DESC);
CREATE INDEX IF NOT EXISTS jobs_deadline_idx   ON jobs (application_deadline);
CREATE INDEX IF NOT EXISTS jobs_source_idx     ON jobs (source);
CREATE INDEX IF NOT EXISTS jobs_search_idx     ON jobs USING gin (search);
CREATE INDEX IF NOT EXISTS jobs_skills_idx     ON jobs USING gin (skills_matched);

-- One row: lets the dashboard show "data as of ..." and lets publish report its last run.
CREATE TABLE IF NOT EXISTS publish_meta (
  id            integer PRIMARY KEY DEFAULT 1 CHECK (id = 1),
  published_at  timestamptz NOT NULL,
  job_count     integer NOT NULL,
  sheet_rows    integer NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
  version     text PRIMARY KEY,
  applied_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO schema_migrations (version) VALUES ('001_init') ON CONFLICT DO NOTHING;
