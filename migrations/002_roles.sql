-- 002_roles.sql
-- BEFORE running: create the roles jobs_publisher and jobs_reader (see Step 3).
-- Then run this file as the project owner role.
-- Idempotent: safe to rerun.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'jobs_publisher') THEN
    RAISE EXCEPTION 'Role jobs_publisher does not exist. Create it first.';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'jobs_reader') THEN
    RAISE EXCEPTION 'Role jobs_reader does not exist. Create it first.';
  END IF;
END
$$;

-- Neither role may create or drop objects, nor create temporary tables.
REVOKE CREATE ON SCHEMA public FROM PUBLIC;

DO $$
BEGIN
  EXECUTE format('REVOKE TEMP ON DATABASE %I FROM PUBLIC', current_database());
  EXECUTE format('REVOKE TEMP ON DATABASE %I FROM jobs_publisher, jobs_reader', current_database());
END
$$;

GRANT USAGE ON SCHEMA public TO jobs_publisher, jobs_reader;

-- Start from a clean slate so reruns converge on the same state.
REVOKE ALL ON jobs, publish_meta, schema_migrations FROM jobs_publisher, jobs_reader;

-- publisher: full refresh of the copy, nothing else
GRANT SELECT, INSERT, UPDATE, DELETE ON jobs, publish_meta TO jobs_publisher;

-- reader: dashboard, SELECT only
GRANT SELECT ON jobs, publish_meta TO jobs_reader;

INSERT INTO schema_migrations (version) VALUES ('002_roles') ON CONFLICT DO NOTHING;