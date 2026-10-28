# PR Violations Investigation Report

**Investigated:** 15 violations across 11 files  
**Result summary:** 14 valid, 1 partially valid (with nuance)

---

## Violation 1 — `docs/09-scheduling-and-setup.md:32`

**Claim:** The Secrets table omits `TELEGRAM_CHAT_ID_JUMALAW98` and `GOOGLE_SHEET_ID_JUMALAW98`, which `config/profiles.yaml` marks as required because the profile is enabled.

**Verdict: VALID**

**Evidence:**  
The Secrets table in `docs/09-scheduling-and-setup.md` (lines 32–44) lists only:
- `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID_JULIET`, `GOOGLE_SERVICE_ACCOUNT_JSON_B64`, `GOOGLE_SHEET_ID_JULIET`

`config/profiles.yaml` at lines 23–30 defines a second profile (`id: jumalaw98`) with `enabled: true` and explicitly requires:
- `sheet_id_env: GOOGLE_SHEET_ID_JUMALAW98`
- `chat_id_env: TELEGRAM_CHAT_ID_JUMALAW98`

The daily.yml workflow passes both of these secrets to the `Run` and `Publish to Neon` steps. A user following doc 09 alone would never know to create those secrets and the run would fail with `ConfigError`.

**Fix:** Add two rows to the Secrets table in `docs/09-scheduling-and-setup.md`:
```
| TELEGRAM_CHAT_ID_JUMALAW98 | Destination chat (jumalaw98 profile) |
| GOOGLE_SHEET_ID_JUMALAW98  | Target spreadsheet (jumalaw98 profile) |
```

---

## Violation 2 — `docs/PUBLISH-INTEGRATION.md:65`

**Claim:** The snippet omits `GOOGLE_SHEET_ID_JUMALAW98`, but `daily.yml`, `tests/test_workflows.py`, and doc 15 all expect the Publish step to receive it.

**Verdict: VALID**

**Evidence:**  
The YAML snippet at lines 60–66 of `docs/PUBLISH-INTEGRATION.md` shows:
```yaml
        env:
          GOOGLE_SERVICE_ACCOUNT_JSON_B64: ${{ secrets.GOOGLE_SERVICE_ACCOUNT_JSON_B64 }}
          GOOGLE_SHEET_ID_JULIET: ${{ secrets.GOOGLE_SHEET_ID_JULIET }}
          NEON_DATABASE_URL_PUBLISHER: ${{ secrets.NEON_DATABASE_URL_PUBLISHER }}
```

The actual `daily.yml` (lines 112–116) passes both:
```yaml
          GOOGLE_SHEET_ID_JULIET: ${{ secrets.GOOGLE_SHEET_ID_JULIET }}
          GOOGLE_SHEET_ID_JUMALAW98: ${{ secrets.GOOGLE_SHEET_ID_JUMALAW98 }}
```

`tests/test_workflows.py` at line 134 explicitly asserts `GOOGLE_SHEET_ID_JUMALAW98` appears in `["Run", "Publish to Neon"]` — meaning the test will fail if the workflow is copied from the guide verbatim.

Doc 15 at line 59 also instructs: _"Pass `GOOGLE_SHEET_ID_JUMALAW98` to both the `Run` and the `Publish` step in `daily.yml`"_.

This is a documentation drift: the guide was written before the second profile was added.

**Fix:** Add `GOOGLE_SHEET_ID_JUMALAW98: ${{ secrets.GOOGLE_SHEET_ID_JUMALAW98 }}` to the snippet's `env:` block.

---

## Violation 3 — `frontend/lib/profiles.ts:42`

**Claim:** `DEFAULT_PROFILE` is not passed through `PROFILE_ALIASES`, so `DASH_DEFAULT_PROFILE=support` no longer maps to `juliet`. Also, `PROFILE_ALIASES` is declared after `DEFAULT_PROFILE`, causing a Temporal Dead Zone (TDZ) error.

**Verdict: PARTIALLY VALID (TDZ claim is INVALID, alias-skip claim is VALID)**

**Evidence:**  
In `frontend/lib/profiles.ts`, the current order is:
```typescript
// line 42
const DEFAULT_PROFILE = (process.env.DASH_DEFAULT_PROFILE ?? "").trim() || "juliet";

// line 46
const PROFILE_ALIASES: Record<string, string> = {
  support: "juliet",
  community: "jumalaw98",
};
```

`DEFAULT_PROFILE` is a `const` initialized via an expression that **does not reference `PROFILE_ALIASES`**, so no TDZ error occurs here. The TDZ claim is wrong — `DEFAULT_PROFILE` simply doesn't use `PROFILE_ALIASES` at all.

However, the alias-skip part is real. In `resolveProfile` (line 52–58):
```typescript
export function resolveProfile(param, available) {
  const wanted = Array.isArray(param) ? param[0] : param;
  const resolved = wanted ? (PROFILE_ALIASES[wanted] ?? wanted) : wanted;
  if (resolved && available.some((p) => p.id === resolved)) return resolved;
  if (available.some((p) => p.id === DEFAULT_PROFILE)) return DEFAULT_PROFILE;  // <-- raw env value
  return available[0]?.id ?? null;
}
```

When `wanted` is `undefined`/missing (no `?profile=` param), the function falls through to the `DEFAULT_PROFILE` check. `DEFAULT_PROFILE` is whatever `DASH_DEFAULT_PROFILE` env var holds — e.g. `"support"` — but it is never aliased. So `available.some((p) => p.id === "support")` returns `false` (since the real id is now `"juliet"`), the fallback silently picks `available[0]`.

**Root cause:** `DEFAULT_PROFILE` is computed once at module load from the raw env value, then used as-is in the alias branch. Aliases are only applied to URL params, not to the env-configured default.

**Fix:** Apply the alias lookup when computing `DEFAULT_PROFILE`, or apply it inline in `resolveProfile` before the `available.some` check:
```typescript
const _rawDefault = (process.env.DASH_DEFAULT_PROFILE ?? "").trim() || "juliet";
// Declare PROFILE_ALIASES first (for readability, not TDZ safety)
const PROFILE_ALIASES: Record<string, string> = { support: "juliet", community: "jumalaw98" };
const DEFAULT_PROFILE = PROFILE_ALIASES[_rawDefault] ?? _rawDefault;
```
Or simply alias inline: `if (available.some((p) => p.id === (PROFILE_ALIASES[DEFAULT_PROFILE] ?? DEFAULT_PROFILE))) ...`

---

## Violation 4 — `src/jobscraper/storage/google_sheets.py:99`

**Claim:** The fallback hard-codes the operator persona's sheet. Any caller that omits `sheet_id` writes to Juliet's Sheet instead of failing.

**Verdict: VALID**

**Evidence:**  
`google_sheets.py` line 99–102:
```python
sheet_id = sheet_id or environ.get("GOOGLE_SHEET_ID_JULIET", "")
if not encoded or not sheet_id:
    raise StorageError("GOOGLE_SERVICE_ACCOUNT_JSON_B64 and GOOGLE_SHEET_ID_JULIET are required")
```

If a caller passes `sheet_id=None` and the environment contains `GOOGLE_SHEET_ID_JULIET`, the method silently uses Juliet's sheet. The multi-profile architecture expects the caller to always pass the correct `sheet_id` from `profile.sheet_id(environ)`. In a multi-profile setup, any bug where a caller omits the sheet_id argument (or passes `None`) would write a second profile's data into the operator's sheet without any error.

The error message further confuses the issue by naming `GOOGLE_SHEET_ID_JULIET` as a requirement, even for non-operator profiles.

**Fix:** Remove the env fallback and require `sheet_id` explicitly:
```python
if not encoded or not sheet_id:
    raise StorageError("GOOGLE_SERVICE_ACCOUNT_JSON_B64 is not set or sheet_id was not provided")
```
The error message should not name a persona-specific env var.

---

## Violation 5 — `tests/test_profiles.py:36`

**Claim:** No test covers `PROFILE_ALIASES` resolution; the existing disabled-profile check (`enabled_profiles(entries, ['community'])` raises `ConfigError`) is now broken because `'community'` maps to `'jumalaw98'` via aliases, which is not in the `TWO` fixture.

**Verdict: VALID**

**Evidence:**  
The `TWO` fixture (lines 27–32) defines profiles with `id: support` and `id: community`.  

The `PROFILE_ALIASES` in `profiles.py` maps:
```python
PROFILE_ALIASES = {"support": "juliet", "community": "jumalaw98"}
```

The test at line 69:
```python
with pytest.raises(ConfigError):
    enabled_profiles(entries, ["community"])
```
This calls `_resolve_alias("community")` → `"jumalaw98"`. Then `by_id["jumalaw98"]` doesn't exist in the fixture → raises `ConfigError("unknown or disabled profile id(s): jumalaw98")`. The test still **passes** — but for the wrong reason. It's testing that `"jumalaw98"` (the alias target) is unknown, not that `"community"` (a configured but disabled profile) is disabled. The disabled-profile contract is not what's being verified.

There are no tests for the happy-path alias cases: `enabled_profiles(entries, ['support'])` should resolve to `juliet`, and `pick_profile(entries, 'community')` should resolve to `jumalaw98`.

**Fix:**
1. Add a test for alias resolution with a fixture that has `juliet`/`jumalaw98` as ids:
   ```python
   def test_aliases_resolve_to_persona_ids(tmp_path):
       text = """
   profiles:
     - {id: juliet, label: Juliet, profile: a.yaml, scoring: b.yaml}
     - {id: jumalaw98, label: Jumalaw, profile: c.yaml, scoring: d.yaml,
        sheet_id_env: SHEET_2, chat_id_env: CHAT_2}
   """
       entries = load_profiles(write(tmp_path, text))
       assert [e.id for e in enabled_profiles(entries, ["support"])] == ["juliet"]
       assert pick_profile(entries, "community").id == "jumalaw98"
   ```
2. Rename the `TWO` fixture ids to `juliet`/`jumalaw98`, or add a separate fixture; then replace the existing `enabled_profiles(entries, ["community"])` test so it tests a genuinely disabled profile using a profile id that doesn't exist in aliases.

---

## Violation 6 — `src/jobscraper/notifications/telegram.py:43`

**Claim:** The error message in the constructor names `TELEGRAM_CHAT_ID_JULIET` even when the missing value is the bot token or another persona's chat ID.

**Verdict: VALID**

**Evidence:**  
`telegram.py` lines 40–43:
```python
if not token or not chat_id:
    raise NotificationError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID_JULIET are required")
```

`TelegramNotifier` is used for every profile's notifications, not just Juliet's. If called for the `jumalaw98` profile (where `chat_id` comes from `TELEGRAM_CHAT_ID_JUMALAW98`) and `token` is missing, the error incorrectly directs the user to check `TELEGRAM_CHAT_ID_JULIET`, which may be set and fine.

**Fix:** Use a generic message:
```python
if not token or not chat_id:
    raise NotificationError("TELEGRAM_BOT_TOKEN and the profile's chat ID are required")
```
Or pass the env var name into the constructor so the message can be specific:
```python
raise NotificationError(f"TELEGRAM_BOT_TOKEN and {chat_id_env_name} are required")
```

---

## Violation 7 — `src/jobscraper/notifications/telegram.py:53`

**Claim:** `from_env` hardcodes `TELEGRAM_CHAT_ID_JULIET`, duplicating the default in `profiles.py` and bypassing the profile's `chat_id_env`. `notify-test` and the scheduled run read different secrets.

**Verdict: VALID**

**Evidence:**  
`telegram.py` line 53:
```python
@classmethod
def from_env(cls, environ: dict[str, str]) -> TelegramNotifier:
    return cls(environ.get("TELEGRAM_BOT_TOKEN", ""), environ.get("TELEGRAM_CHAT_ID_JULIET", ""))
```

This `from_env` method is persona-specific — it only ever reads Juliet's chat ID. Any `notify-test` or one-off command that uses `TelegramNotifier.from_env()` always messages Juliet's chat, even if run in a jumalaw98 context. Meanwhile, the scheduled run resolves the profile's `chat_id_env` from `profiles.yaml` and reads the correct per-profile secret.

There are two issues:
1. A constant `"TELEGRAM_CHAT_ID_JULIET"` is duplicated here and in `ProfileEntry.chat_id_env` default in `profiles.py` line 53.
2. `from_env` with no profile context can only be correct for the operator profile.

**Fix:** Either deprecate `from_env` and require callers to resolve the chat ID from the profile object first, or import a shared constant:
```python
# profiles.py
OPERATOR_CHAT_ID_ENV = "TELEGRAM_CHAT_ID_JULIET"

# telegram.py
from jobscraper.profiles import OPERATOR_CHAT_ID_ENV


@classmethod
def from_env(cls, environ: dict[str, str]) -> TelegramNotifier:
    return cls(environ.get("TELEGRAM_BOT_TOKEN", ""), environ.get(OPERATOR_CHAT_ID_ENV, ""))
```
This ensures both usages stay in sync if the constant is ever changed.

---

## Violation 8 — `.github/workflows/daily.yml:61`

**Claim:** The workflow reads only persona-suffixed secrets; until those GitHub secrets are created, the run fails. The failure alert then posts to an empty chat ID and is silently skipped.

**Verdict: VALID (operational risk, not a code bug)**

**Evidence:**  
`daily.yml` lines 55–65 (Run step) and lines 112–116 (Publish to Neon step) reference:
- `secrets.GOOGLE_SHEET_ID_JULIET` (renamed from whatever prior name, if any)
- `secrets.GOOGLE_SHEET_ID_JUMALAW98`
- `secrets.TELEGRAM_CHAT_ID_JULIET` (renamed from prior name)
- `secrets.TELEGRAM_CHAT_ID_JUMALAW98`

If a repo previously had secrets named `GOOGLE_SHEET_ID` or `TELEGRAM_CHAT_ID` (generic names), those old secrets are no longer referenced. The new names must exist before this PR is merged or the next scheduled run will fail.

Additionally, the "Alert on failure" step (lines 120–134) uses `TELEGRAM_CHAT_ID_JULIET` directly from env. If that secret doesn't exist, `TELEGRAM_CHAT_ID_JULIET` is empty and the curl call posts to an empty chat_id — Telegram returns 400 and `continue-on-error: true` swallows it silently.

**Fix:** This is a deployment/operational concern. No code change fixes it. The required actions are:
1. Rename (or create) GitHub repo secrets to match the new names before merging.
2. Document this in the PR description as a required pre-merge step.
3. Optionally: add a pre-flight step that checks required secrets are non-empty before running.

---

## Violation 9 — `config/profiles.yaml:15`

**Claim:** Renaming juliet's env names has no fallback. Until `GOOGLE_SHEET_ID_JULIET` and `TELEGRAM_CHAT_ID_JULIET` GitHub secrets exist, the run fails.

**Verdict: VALID (operational/deployment risk)**

**Evidence:**  
`config/profiles.yaml` lines 14–18:
```yaml
  - id: juliet
    sheet_id_env: GOOGLE_SHEET_ID_JULIET
    chat_id_env: TELEGRAM_CHAT_ID_JULIET
```

These were previously named with different convention (e.g., `GOOGLE_SHEET_ID`, `TELEGRAM_CHAT_ID`, or `_SUPPORT`). The profiles.yaml has been updated to use the persona-suffixed names, but the GitHub repo secrets must be renamed to match **before** any scheduled run.

**Fix:** Same as Violation 8 — this is a migration task, not a code bug. Required actions:
1. Rename GitHub secrets `GOOGLE_SHEET_ID` → `GOOGLE_SHEET_ID_JULIET`, `TELEGRAM_CHAT_ID` → `TELEGRAM_CHAT_ID_JULIET` (or whatever the old names were) prior to merging.
2. Call it out explicitly in the PR description and in a migration note appended to doc 15.

---

## Violation 10 — `config/profiles.yaml:38`

**Claim:** The onboarding comment says three keys are required, but the loader defaults them. A new persona that omits `sheet_id_env` or `chat_id_env` silently falls back to juliet's secret names.

**Verdict: VALID**

**Evidence:**  
`config/profiles.yaml` lines 38–47 (the "Adding a new person" comment):
```yaml
# 2. Add an entry below with id, label (Title Case), enabled, profile, scoring,
#    sheet_id_env, chat_id_env, digest_title, and optional sources allowlist.
```
This comment implies `sheet_id_env` and `chat_id_env` are required fields.

However, `profiles.py` line 118–120:
```python
sheet_id_env = (_text(raw, "sheet_id_env", where, "GOOGLE_SHEET_ID_JULIET"),)
chat_id_env = (_text(raw, "chat_id_env", where, "TELEGRAM_CHAT_ID_JULIET"),)
```

The third positional argument to `_text()` is a default value. If a new profile omits `sheet_id_env`, it silently inherits `"GOOGLE_SHEET_ID_JULIET"`. The `_check_unique` function catches this only while both juliet and the new profile are enabled (duplicate `sheet_id_env` check), but if only the new profile is enabled and juliet is not, the collision is missed.

**Fix:** Two options:
1. Drop the defaults from `_entry()` and make the keys required (raises `ConfigError` if missing). Update the comment to accurately reflect this.
2. Keep the defaults but update the comment to say: _"If omitted, `sheet_id_env` defaults to `GOOGLE_SHEET_ID_JULIET` and `chat_id_env` to `TELEGRAM_CHAT_ID_JULIET` — you almost certainly want to override these."_

Option 1 is safer and matches the intent of the violation's recommendation.

---

## Violation 11 — `src/jobscraper/profiles.py:51`

**Claim:** The no-`profiles.yaml` compatibility path (legacy mode) now requires the renamed secrets, so existing legacy installs fail.

**Verdict: VALID**

**Evidence:**  
`profiles.py` lines 70–77 (`legacy_profile` function):
```python
def legacy_profile(profile: Path, scoring: Path) -> ProfileEntry:
    return ProfileEntry(
        id=LEGACY_ID,  # "juliet"
        label="Juliet",
        profile_path=profile,
        scoring_path=scoring,
        digest_title=LEGACY_DIGEST_TITLE,
        # sheet_id_env defaults to "GOOGLE_SHEET_ID_JULIET"
        # chat_id_env defaults to "TELEGRAM_CHAT_ID_JULIET"
    )
```

Pre-PR, the legacy install presumably used environment variables like `GOOGLE_SHEET_ID` (generic) or possibly `TELEGRAM_CHAT_ID`. The `legacy_profile()` function now silently requires `GOOGLE_SHEET_ID_JULIET` and `TELEGRAM_CHAT_ID_JULIET` via the `ProfileEntry` defaults.

An existing user who deletes `config/profiles.yaml` to run in legacy mode (as the doc promises: _"Delete this file to run the old single-profile setup unchanged"_) will hit `ConfigError: profile 'juliet': GOOGLE_SHEET_ID_JULIET is not set` if they haven't renamed their env vars.

**Fix:** Two options:
1. For legacy mode only, fall back to the old generic names with a deprecation warning:
   ```python
   def legacy_profile(profile: Path, scoring: Path) -> ProfileEntry:
       # Try the new name first; accept the old generic name with a deprecation log
       sheet_env = "GOOGLE_SHEET_ID_JULIET"  # new canonical name
       chat_env = "TELEGRAM_CHAT_ID_JULIET"
       return ProfileEntry(id=LEGACY_ID, ..., sheet_id_env=sheet_env, chat_id_env=chat_env)
   ```
   And in `ProfileEntry.sheet_id()` / `chat_id()`, add fallback logic for old names.
2. Document that legacy users must rename their env vars before upgrading — noting the migration in doc 09 and doc 15.

Option 2 is simpler; Option 1 is smoother for existing users.

---

## Violation 12 — `src/jobscraper/profiles.py:118`

**Claim:** The default env var names are hard-coded to the operator's `JULIET` secrets for every profile. They should be derived from the profile id.

**Verdict: VALID**

**Evidence:**  
`profiles.py` lines 118–120:
```python
sheet_id_env = (_text(raw, "sheet_id_env", where, "GOOGLE_SHEET_ID_JULIET"),)
chat_id_env = (_text(raw, "chat_id_env", where, "TELEGRAM_CHAT_ID_JULIET"),)
```

Compare how `digest_title` is derived (line 121):
```python
digest_title = (_text(raw, "digest_title", where, f"NEW {label.upper()} JOBS"),)
```

`digest_title` derives from the profile's `label`. By analogy, `sheet_id_env` and `chat_id_env` could derive from the profile's `id`:
```python
sheet_id_env = (_text(raw, "sheet_id_env", where, f"GOOGLE_SHEET_ID_{profile_id.upper()}"),)
chat_id_env = (_text(raw, "chat_id_env", where, f"TELEGRAM_CHAT_ID_{profile_id.upper()}"),)
```

As-is, any new profile that omits those keys silently shares the operator's secrets, which would cause the duplicate-env-name check in `_check_unique` to fail — but only if the operator profile is also enabled. If the file contains only the new profile, the collision is undetected.

**Fix:** Derive defaults from `profile_id` as described. This also aligns with the principle of least surprise for anyone adding a new profile without explicitly specifying env names.

---

## Violation 13 — `src/jobscraper/profiles.py:180`

**Claim:** Aliases are applied before checking whether the id exists, so a configured profile with `id: support` or `id: community` can never be selected with `--for` or `--only`.

**Verdict: VALID**

**Evidence:**  
`profiles.py` lines 179–187 (`enabled_profiles` function):
```python
by_id = {e.id: e for e in entries}
if only:
    resolved = [_resolve_alias(p) for p in only]  # "support" → "juliet"
    bad = [p for p in resolved if p not in by_id or not by_id[p].enabled]
    ...
    return [by_id[p] for p in dict.fromkeys(resolved)]
```

If someone has a `profiles.yaml` with `id: support` (a configured real profile id, not an alias target), and runs `--for support`:
1. `_resolve_alias("support")` returns `"juliet"`
2. `by_id["juliet"]` doesn't exist → `"juliet"` lands in `bad`
3. Raises `ConfigError: unknown or disabled profile id(s): juliet`

The configured profile `support` can never be reached via `--for support` because it's always aliased away.

**Fix:** Check the configured ids first; only alias if the id is not directly found:
```python
def enabled_profiles(entries, only=None):
    by_id = {e.id: e for e in entries}
    if only:
        resolved = []
        for p in only:
            if p in by_id:
                resolved.append(p)  # exact match — use as-is
            else:
                resolved.append(_resolve_alias(p))  # alias fallback
        bad = [p for p in resolved if p not in by_id or not by_id[p].enabled]
        ...
```

This is a real logic bug: anyone who literally named their profile `support` or `community` would hit an impenetrable error with no useful message.

---

## Violation 14 — `docs/15-multi-profile.md:58`

**Claim:** The setup section uses `juliet`/`jumalaw98`, but the Database migration paragraph still says to backfill `support`.

**Verdict: VALID**

**Evidence:**  
`docs/15-multi-profile.md` line 64 (Database migration section):
```
Run `migrations/003_profile.sql` on the Neon `dev` branch, then production, with the direct
connection string. It backfills existing rows to profile `support`. If your first profile id is
not `support`, change both marked `(A)` lines first.
```

But `migrations/003_profile.sql` line 14 already says `'juliet'`:
```sql
UPDATE jobs SET profile = 'juliet' WHERE profile IS NULL;   -- (A)
```

The migration uses `'juliet'`, not `'support'`. The doc is outdated — it still references the old draft where the operator's profile was `id: support`. The current code uses `id: juliet`.

The instruction _"If your first profile id is not `support`, change both marked `(A)` lines first"_ should read _"If your first profile id is not `juliet`"_.

**Fix:** Update the migration paragraph in doc 15:
```
It backfills existing rows to profile 'juliet'. If your operator profile id is different,
change both lines marked (A) before running.
```
Also explain the existing `support`→`juliet` data conversion for anyone who ran the old version.

---

## Violation 15 — `migrations/003_profile.sql:14`

**Claim:** This migration only updates NULL rows. Databases that already ran the old `003_profile.sql` (which backfilled rows to `'support'`) have non-NULL `support` rows that won't be migrated to `'juliet'`.

**Verdict: VALID**

**Evidence:**  
`migrations/003_profile.sql` lines 14–16:
```sql
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS profile text;
UPDATE jobs SET profile = 'juliet' WHERE profile IS NULL;   -- (A)
ALTER TABLE jobs ALTER COLUMN profile SET NOT NULL;
```

An earlier version of the migration script (based on the doc 15 text and the comment in the SQL: _"No default on purpose: a publish that forgets `profile` must fail, not land in 'support'"_) used `'support'` as the backfill value. Any database that ran that version has rows with `profile = 'support'`. Re-running this migration leaves those rows untouched because `WHERE profile IS NULL` doesn't match `'support'`.

The result: after migration, the database has `profile = 'support'` rows, but:
- `config/profiles.yaml` has `id: juliet`, not `id: support`
- The dashboard query `SELECT profile FROM publish_meta` returns `'support'`
- The frontend's `resolveProfile` expects `'juliet'`, so Juliet's published data becomes unreachable

**Fix:** Add a migration step to rename existing `'support'` rows to `'juliet'` (or whatever new id), handling potential key conflicts:
```sql
-- Migrate legacy 'support' rows to the new operator id 'juliet'
-- Handle potential conflict: if a 'juliet' row already exists in publish_meta,
-- keep it and drop the stale 'support' row.
UPDATE jobs SET profile = 'juliet' WHERE profile = 'support';
-- For publish_meta (primary key = profile), conflict-safe approach:
INSERT INTO publish_meta SELECT 'juliet', published_at FROM publish_meta WHERE profile = 'support'
  ON CONFLICT (profile) DO NOTHING;
DELETE FROM publish_meta WHERE profile = 'support';
```
This must run before the `WHERE profile IS NULL` backfill, and the migration should document the assumption about what prior state may exist.

---

## Summary of Findings

| # | Location | Valid? | Severity | Type |
|---|---|---|---|---|
| 1 | docs/09-scheduling-and-setup.md:32 | ✅ Valid | P2 | Doc gap |
| 2 | docs/PUBLISH-INTEGRATION.md:65 | ✅ Valid | P3 | Doc drift |
| 3 | frontend/lib/profiles.ts:42 | ✅ Valid (partial) | P2 | Logic bug (TDZ claim wrong) |
| 4 | src/jobscraper/storage/google_sheets.py:99 | ✅ Valid | P2 | Silent wrong-sheet bug |
| 5 | tests/test_profiles.py:36 | ✅ Valid | P2 | Missing test + broken existing test |
| 6 | src/jobscraper/notifications/telegram.py:43 | ✅ Valid | P3 | Misleading error message |
| 7 | src/jobscraper/notifications/telegram.py:53 | ✅ Valid | P2 | Hardcoded persona secret |
| 8 | .github/workflows/daily.yml:61 | ✅ Valid | P2 | Operational/deployment risk |
| 9 | config/profiles.yaml:15 | ✅ Valid | P2 | Operational/deployment risk |
| 10 | config/profiles.yaml:38 | ✅ Valid | P3 | Silent bad default + misleading comment |
| 11 | src/jobscraper/profiles.py:51 | ✅ Valid | P1 | Legacy install breakage |
| 12 | src/jobscraper/profiles.py:118 | ✅ Valid | P2 | Wrong defaults for non-operator profiles |
| 13 | src/jobscraper/profiles.py:180 | ✅ Valid | P2 | Logic bug: configured ids aliased away |
| 14 | docs/15-multi-profile.md:58 | ✅ Valid | P2 | Doc uses stale id ('support' vs 'juliet') |
| 15 | migrations/003_profile.sql:14 | ✅ Valid | P1 | Data not migrated on re-run |

### Most critical (P1 — blocks correct operation)

- **Violation 11 (`profiles.py:51`):** Legacy installs without `profiles.yaml` fail immediately because `legacy_profile()` now requires `GOOGLE_SHEET_ID_JULIET` / `TELEGRAM_CHAT_ID_JULIET` which old installs don't have.
- **Violation 15 (`migrations/003_profile.sql:14`):** Any DB that ran the old migration has `profile='support'` rows that remain `'support'` after this rerun, making the operator's data invisible to the dashboard.

### Most insidious (silent wrong behavior)

- **Violation 4 (`google_sheets.py:99`):** Omitting `sheet_id` silently writes to the operator's sheet.
- **Violation 12 (`profiles.py:118`):** New profiles without `sheet_id_env` silently inherit the operator's secrets.
- **Violation 13 (`profiles.py:180`):** Profiles with `id: support` or `id: community` can never be selected via `--for`, but get a confusing error about a different id.
- **Violation 3 (`profiles.ts:42`):** Old `DASH_DEFAULT_PROFILE=support` env setting silently falls through to `available[0]` instead of resolving to `juliet`.
