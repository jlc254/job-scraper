# Profile Switch Visibility Investigation Report

**Date:** 2026-10-28  
**Task:** Confirm both profiles are active and visible for switching in the frontend dashboard  
**Verdict:** ✅ YES — both profiles are active and the profile switcher will show both, **provided both have been published to the Neon database.**

---

## Summary Answer

Both profiles (`support` and `community`) are defined as `enabled: true` in `config/profiles.yaml`. The backend pipeline will process both. The frontend `ProfileSwitcher` component renders a link for every profile returned by `listProfiles()`, with no visibility filter other than: **the profile must have a row in the `publish_meta` table** (i.e. it must have been published at least once). If both profiles have been published, the switcher is fully functional. There is no `isActive`, `status`, or role gate anywhere in the switcher chain.

---

## Q1 — Backend Profile Definition: Are Both Profiles Marked Active?

**YES.**

**File:** `config/profiles.yaml`

```yaml
profiles:
  - id: support
    label: Customer support
    enabled: true          # ← active
    ...

  - id: community
    label: Community and programs
    enabled: true          # ← active
    ...
```

**File:** `src/jobscraper/profiles.py` — `ProfileEntry` dataclass

The `enabled` field defaults to `True`. The `load_profiles()` function parses the YAML and passes through all entries (enabled or not) to `_check_unique`. The `enabled_profiles()` function then returns only entries where `enabled is True`. Both profiles satisfy this; both will be processed by the pipeline.

An integration test (`tests/test_profiles.py::test_every_shipped_profile_is_enabled_and_resolves_its_own_secrets`) explicitly asserts:

```python
assert [e.id for e in enabled_profiles(entries)] == ["support", "community"]
```

This test would fail if either profile were disabled.

**Database schema:** `migrations/003_profile.sql` adds a `profile` column (NOT NULL, constrained to `^[a-z][a-z0-9_]{0,23}$`) to both `jobs` and `publish_meta`, keying all rows by profile. There is no `is_active` column on profiles — activation is config-file-only.

---

## Q2 — Frontend Profile Switcher: Which Component Renders It?

**File:** `frontend/components/ProfileSwitcher.tsx`

```tsx
export default function ProfileSwitcher({ profiles, current }: { profiles: ProfileInfo[]; current: string }) {
  if (profiles.length < 2) return null;   // ← hidden when only one profile exists
  return (
    <nav aria-label="Profile" ...>
      {profiles.map((p) => (
        <Link key={p.id} href={`/?profile=${encodeURIComponent(p.id)}`} ...>
          {p.label}
          {active ? " (viewing)" : ""}
        </Link>
      ))}
    </nav>
  );
}
```

It is a pure server component — no client state, no `useEffect`. It renders a `<nav>` with one `<Link>` per profile. Switching resets filters (by design: the href goes to `/?profile=...` with no carry-over).

**File:** `frontend/app/page.tsx` — it is mounted in the sidebar:

```tsx
const profiles = await listProfiles();
const profile = resolveProfile(raw.profile, profiles);
...
<ProfileSwitcher profiles={profiles} current={profile} />
```

---

## Q3 — Is There Any Filtering Logic That Would Hide a Profile?

**No hidden profiles are possible once published.** The only gate is existence in `publish_meta`.

**File:** `frontend/lib/profiles.ts` — `loadProfiles()`:

```ts
async function loadProfiles(): Promise<ProfileInfo[]> {
  const rows = await query<{ profile: string; published_at: string | null }>(
    `SELECT profile,
            to_char(published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS published_at
       FROM publish_meta ORDER BY profile`,
  );
  ...
  return rows.map((r) => ({
    id: r.profile,
    label: labels.get(r.profile) ?? r.profile,
    publishedAt: r.published_at,
  }));
}
```

The query is `SELECT * FROM publish_meta ORDER BY profile`. There is:
- **No `WHERE` clause** — all rows are returned
- **No `is_active`, `status`, or `role` filter**
- **No client-side Redux/Zustand/Context state** — this is a Next.js server component, profiles are fetched on every request (with a 60-second cache)

The `resolveProfile()` function (also in `profiles.ts`) selects the active profile from the list. It falls back to `DASH_DEFAULT_PROFILE` env var (default: `"support"`) if the requested profile isn't found — it does not hide profiles.

---

## Q4 — Are Both Profiles Present in the Data Source the Dashboard Consumes?

**Conditionally YES — depends on whether both have been published.**

The dashboard reads `publish_meta` from the Neon database (configured via `DATABASE_URL` in `frontend/.env.local`). The `publish_meta` table gets one row per profile, written when the `publish` CLI command runs for that profile.

- `frontend/.env.local` sets `DATABASE_URL` pointing to the live Neon pooler endpoint and `DASH_PROFILE_LABELS=support=Customer support,community=Community and programs`. Both profile ids are mapped to their display labels.
- The `community` profile's row in `publish_meta` is created only after `python main.py publish --for community` (or equivalent) has run at least once successfully.

If the `community` profile has never been published, `publish_meta` will have only a `support` row, `listProfiles()` returns a single-element array, and `ProfileSwitcher` returns `null` (hidden, because `profiles.length < 2`).

The last known publish output files in `output/` (`jobs-community-20261026-120145.csv` through `jobs-community-20261027-104656.csv`) strongly suggest the `community` profile has been published. If those runs completed successfully and the Neon publish step ran (not just the CSV), both rows exist in `publish_meta`.

---

## Q5 — Is There Any Frontend State That Gates Which Profiles Are Shown?

**No.** There is no Redux, Zustand, React Context, or `useState` involved in profile listing or the switcher. The entire flow is server-side:

1. `page.tsx` (server component) calls `listProfiles()` (cached async function, 60s revalidation)
2. `listProfiles()` queries `publish_meta` directly
3. The result is passed as a prop to `ProfileSwitcher` (server component)
4. `ProfileSwitcher` renders all profiles in the list

There is no client-side gate, no auth check, and no feature flag.

---

## Evidence Summary

| Item | File | Finding |
|------|------|---------|
| Both profiles `enabled: true` | `config/profiles.yaml` | ✅ |
| Backend `enabled_profiles()` returns both | `src/jobscraper/profiles.py` | ✅ |
| Integration test asserts both enabled | `tests/test_profiles.py:test_every_shipped_profile_is_enabled_and_resolves_its_own_secrets` | ✅ |
| DB schema supports both | `migrations/003_profile.sql` | ✅ |
| `ProfileSwitcher` renders all profiles (no filter) | `frontend/components/ProfileSwitcher.tsx` | ✅ |
| `listProfiles()` has no WHERE filter | `frontend/lib/profiles.ts` | ✅ |
| No client state gating visibility | `frontend/app/page.tsx`, `ProfileSwitcher.tsx` | ✅ |
| Display labels configured for both | `frontend/.env.local` (`DASH_PROFILE_LABELS`) | ✅ |
| Switcher hidden if only 1 profile in DB | `ProfileSwitcher.tsx` line 3 | ⚠️ conditional |
| Community publish output files exist | `output/jobs-community-*.csv` | 🟡 CSV only, DB not verifiable from code |

---

## Conclusions

**Both profiles are correctly defined as active in the backend config and code.** The switcher will show both profiles with their display labels ("Customer support" and "Community and programs") as long as both have rows in the Neon `publish_meta` table.

The only remaining uncertainty is **whether the `community` profile's publish run has landed in the Neon database** (as opposed to only generating CSVs). The CSV output files show the scraper ran for `community`, but a Neon publish requires the `publish` CLI command to run against the live database, which cannot be confirmed from code inspection alone.

---

## Recommendations (No Code Changes Needed)

1. **Verify `publish_meta` in Neon:** Run `SELECT profile, published_at, job_count FROM publish_meta ORDER BY profile;` on the Neon database. You should see two rows: one for `support` and one for `community`. If only one row exists, re-run the publish step for the missing profile.

2. **If `community` row is missing:** Run `python main.py publish --for community` (with the correct environment variables set: `GOOGLE_SHEET_ID_COMMUNITY`, `TELEGRAM_CHAT_ID_COMMUNITY`) to publish the community profile to Neon. After the next dashboard load (or within 60 seconds of cache expiry), the switcher will appear automatically.

3. **No code changes are required.** The filtering logic, UI rendering, and data model are all correctly implemented for multi-profile visibility.
