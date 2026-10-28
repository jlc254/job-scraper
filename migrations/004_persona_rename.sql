-- 004_persona_rename.sql
-- Renames profile ids from role-based (support/community) to persona-based
-- (juliet/jumalaw98) in existing rows. Run after 003_profile.sql. Idempotent.
--
-- 003 only backfills NULL rows to the operator id; it does not rename rows that
-- already carry 'support' or 'community'. This migration does, and guards against
-- PK conflicts on (profile, job_id) / profile when the target id already exists.

BEGIN;

-- jobs: drop rows that would collide with an already-present target row, then rename.
DELETE FROM jobs
 WHERE profile = 'support'
   AND job_id IN (SELECT job_id FROM jobs WHERE profile = 'juliet');
DELETE FROM jobs
 WHERE profile = 'community'
   AND job_id IN (SELECT job_id FROM jobs WHERE profile = 'jumalaw98');

UPDATE jobs SET profile = 'juliet' WHERE profile = 'support';
UPDATE jobs SET profile = 'jumalaw98' WHERE profile = 'community';

-- publish_meta: PK is profile, so drop a source row only if its target already exists.
DELETE FROM publish_meta WHERE profile = 'support'
  AND EXISTS (SELECT 1 FROM publish_meta WHERE profile = 'juliet');
DELETE FROM publish_meta WHERE profile = 'community'
  AND EXISTS (SELECT 1 FROM publish_meta WHERE profile = 'jumalaw98');

UPDATE publish_meta SET profile = 'juliet' WHERE profile = 'support';
UPDATE publish_meta SET profile = 'jumalaw98' WHERE profile = 'community';

INSERT INTO schema_migrations (version) VALUES ('004_persona_rename') ON CONFLICT DO NOTHING;

COMMIT;