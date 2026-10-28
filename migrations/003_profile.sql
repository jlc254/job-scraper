-- 003_profile.sql  (doc 15)
-- Adds the `profile` dimension: jobs are keyed by (profile, job_id) and publish_meta has one
-- row per profile. Run as the project owner role on the DIRECT connection string, on the dev
-- branch first, then production. Idempotent: safe to rerun.
--
-- BEFORE running: the literal 'juliet' below is the id of your EXISTING (operator) profile. It must equal
-- the first profile id in config/profiles.yaml. To use another id, change it in the two
-- places marked (A) before the first run. Existing rows are backfilled to it.

BEGIN;

-- jobs ---------------------------------------------------------------------------------------
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS profile text;
UPDATE jobs SET profile = 'juliet' WHERE profile IS NULL;                      -- (A)
ALTER TABLE jobs ALTER COLUMN profile SET NOT NULL;
-- No default on purpose: a publish that forgets `profile` must fail, not land in 'support'.

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_index i
    JOIN pg_class c ON c.oid = i.indrelid
    WHERE c.relname = 'jobs' AND i.indisprimary
      AND (SELECT array_agg(a.attname::text ORDER BY k.ord)
           FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, ord)
           JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = k.attnum)
          = ARRAY['profile', 'job_id']
  ) THEN
    ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_pkey;
    ALTER TABLE jobs ADD CONSTRAINT jobs_pkey PRIMARY KEY (profile, job_id);
  END IF;
END
$$;

ALTER TABLE jobs DROP CONSTRAINT IF EXISTS jobs_profile_format;
ALTER TABLE jobs ADD CONSTRAINT jobs_profile_format CHECK (profile ~ '^[a-z][a-z0-9_]{0,23}$');

-- Every dashboard query filters by profile first, so the profile leads each composite index.
DROP INDEX IF EXISTS jobs_tier_score_idx;
DROP INDEX IF EXISTS jobs_score_idx;
DROP INDEX IF EXISTS jobs_first_seen_idx;
CREATE INDEX IF NOT EXISTS jobs_profile_tier_score_idx
  ON jobs (profile, match_tier, match_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS jobs_profile_score_idx
  ON jobs (profile, match_score DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS jobs_profile_first_seen_idx
  ON jobs (profile, first_seen DESC);
-- jobs_search_idx (GIN), jobs_skills_idx (GIN), jobs_deadline_idx and jobs_source_idx stay:
-- they are used after the profile filter narrows the rows.

-- publish_meta -----------------------------------------------------------------------------------
ALTER TABLE publish_meta ADD COLUMN IF NOT EXISTS profile text;
UPDATE publish_meta SET profile = 'juliet' WHERE profile IS NULL;              -- (A)
ALTER TABLE publish_meta ALTER COLUMN profile SET NOT NULL;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'publish_meta' AND column_name = 'id'
  ) THEN
    ALTER TABLE publish_meta DROP CONSTRAINT IF EXISTS publish_meta_pkey;
    ALTER TABLE publish_meta DROP CONSTRAINT IF EXISTS publish_meta_id_check;
    ALTER TABLE publish_meta DROP COLUMN id;
    ALTER TABLE publish_meta ADD CONSTRAINT publish_meta_pkey PRIMARY KEY (profile);
  END IF;
END
$$;

INSERT INTO schema_migrations (version) VALUES ('003_profile') ON CONFLICT DO NOTHING;

COMMIT;

-- Grants: ALTER TABLE keeps existing privileges, so 002_roles.sql needs no change.
-- Rollback (copy-only database): DROP TABLE jobs, publish_meta; rerun 001 and 002, then publish.
-- Verify:
--   SELECT profile, count(*) FROM jobs GROUP BY 1;
--   SELECT * FROM publish_meta;
