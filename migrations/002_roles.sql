-- 002_roles.sql
-- BEFORE running: create two roles in the Neon console (or CLI), named exactly:
--   jobs_publisher   (used only by the GitHub Actions publish step)
--   jobs_reader      (used only by the dashboard on Vercel)
-- Neon issues their passwords. Then run this file as the project owner role.
-- Idempotent: safe to rerun.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'jobs_publisher') THEN
    RAISE EXCEPTION 'Role jobs_publisher does not exist. Create it in the Neon console first.';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'jobs_reader') THEN
    RAISE EXCEPTION 'Role jobs_reader does not exist. Create it in the Neon console first.';
  END IF;
END
$$;

-- Neither role may create or drop objects.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO jobs_publisher, jobs_reader;

-- Start from a clean slate so reruns converge on the same state.
REVOKE ALL ON jobs, publish_meta, schema_migrations FROM jobs_publisher, jobs_reader;

-- publisher: full refresh of the copy, nothing else
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs, publish_meta TO jobs_publisher;

-- reader: dashboard, SELECT only
GRANT SELECT ON jobs, publish_meta TO jobs_reader;

INSERT INTO schema_migrations (version) VALUES ('002_roles') ON CONFLICT DO NOTHING;
