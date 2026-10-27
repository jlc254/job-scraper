# 15. Multi-profile

One pipeline serving two people. Status: **code written, not run against live services.** Read "What is verified" before trusting it.

## Purpose
Run the same fetch for more than one person, each with their own target roles, scoring, Google Sheet, Telegram chat and dashboard view. The first profile is yours (customer support). The second is a different person in Kenya seeking remote roles open to anywhere (community, programs, events, DevRel).

## Decisions (add to the log in doc 00)
| ID | Decision | Reason |
|---|---|---|
| D29 | Fetching is shared. Everything a person owns is per profile: profile and scoring files, Sheet, Telegram chat, digest title, Neon rows | Sources are polite and rate-limited, so they are fetched once. A Sheet is shared per file, so two people on one Sheet would see each other's notes |
| D30 | Profiles are listed in `config/profiles.yaml`. With no file, the old single-profile setup runs unchanged. A profile `id` is permanent | Backward compatible. The id is stored in Neon and in dashboard links |
| D31 | The operator is the first profile in the file. Its Sheet holds source-health history and it alone receives source-health alerts. Other people still see the RUN line in their digest | Alerts about broken adapters are the owner's job, not the second person's |
| D32 | Neon rows are keyed `(profile, job_id)`. `publish_meta`, the row-count guard and the stale-row delete are all per profile | One profile publishing or failing can never delete another's rows |
| D33 | The dashboard has no login (owner's decision). A profile switcher selects the view through `?profile=` | See "Dashboard without a login" for what this exposes |
| D34 | Rows of a profile that is no longer enabled are pruned from Neon, but only on a full publish where every profile published cleanly | A failed Sheet read or `--only` run must never delete data |
| D35 | Location points stay at the defaults, so on-site Nairobi (20) and other Kenyan cities (16) still score for both profiles | Owner's decision |
| D36 | Himalayas treats `EMEA` as `unclear`, like Jobicy and We Work Remotely. This changes the first profile's output too | Doc 06 says EMEA is scored, not excluded. The three adapters disagreed |
| D37 | `skills.py` and `explain.py` were not reviewed and are not changed. The second profile's YAML avoids risky synonyms, and diagnostic tests check how the real extractor behaves | Safest choice without seeing them |
| D38 | Scoring and profile models reject unknown keys, and industry keys are lowercased | The second profile's files had seven blocks that were silently ignored |
| D39 | The `postgres` storage backend supports one profile only | See "Not changed" |

## How a run works now
```text
fetch once (shared)  ->  evaluate source health once  ->  for each enabled profile:
   copy results, narrow by profile sources -> normalize -> filters -> dedupe (own Sheet)
   -> score -> save -> digest to own chat -> refresh own Dash tabs
-> one source-health alert to the operator -> exit with the worst code
```
- A failure in one profile is contained. The exit code is the worst across profiles (storage outranks delivery outranks unexpected).
- `process_jobs` writes counts onto its `SourceResult`s, so each profile gets a deep copy. Health is judged before the copies are made.
- The "already seen" check is per profile because each profile has its own Sheet and Excluded tab. A job excluded for one person is still evaluated for the other.
- `Job`, `normalize_job`, `Deduper` and `Scorer` use `model_copy`, so profiles cannot corrupt each other's jobs. Fingerprints stay profile-independent.

### Per-profile sources
A profile may name `sources:` in `profiles.yaml`, an allowlist of source ids. Without it the profile sees every enabled source. Fetching is still shared: a source is fetched once per run if any profile names it, and each profile then keeps only the jobs whose `source` is on its list. `validate_profile_sources` refuses an id that is not in `sources.yaml`, because a typo would silently empty that profile's digest.

The fetch set of a run is the **union of the active profiles' allowlists** (or, if any active profile has no `sources:`, every enabled source). A configured source that no profile references costs no request. An explicit `--sources` flag overrides the profiles for that one run.

The shipped file uses this to widen one profile without touching the other:

```yaml
  - id: support
    sources: [himalayas, jobicy, weworkremotely]              # unchanged fetch set
  - id: community
    sources: [himalayas, jobicy, weworkremotely, weworkremotely_categories]
```

The community profile names `weworkremotely` as well, so the support feed URL is requested **once** per run and both profiles read from it; `weworkremotely_categories` carries the remaining 6 category feeds plus the site-wide feed.

`weworkremotely` and `weworkremotely_categories` are the same adapter class under two ids (`WeWorkRemotelyCategoriesAdapter` subclasses the support one), so the parser and guid format are identical and cross-feed duplicates still merge. Source-health alerts still go to the operator, so the categories id can appear in a health alert even though the support profile never scores its jobs.

Depth settings are different: `max_pages`/`page_size` on Himalayas and `query_params.count` on Jobicy live on a single shared source, so they apply to every profile. Raising them widens both pools (support's filters are unchanged, so it can only gain an older ad it would otherwise not have seen). Splitting those into a second id would double the requests to one host, which Jobicy's one-request-per-hour guidance forbids, so the shipped config keeps one request each: Jobicy `count: 100`, Himalayas `max_pages: 10`.

## Setup for the second person
1. **Sheet.** Create a new Google Sheet. Rename the first tab to exactly `Jobs`. Share it with the same service account as Editor. Add the `application_status` dropdown (New, Saved, Applied, Interview, Offer, Rejected, Ignored). Copy the Sheet id. Do not use link sharing.
2. **Telegram.** They message your bot once, then you read their chat id from `getUpdates` (privately, the URL contains your token). One bot serves both chats.
3. **GitHub secrets.** Add `GOOGLE_SHEET_ID_COMMUNITY` and `TELEGRAM_CHAT_ID_COMMUNITY`.
4. **Workflow.** Pass `GOOGLE_SHEET_ID_COMMUNITY` to both the `Run` and the `Publish` step in `daily.yml`, and `TELEGRAM_CHAT_ID_COMMUNITY` to `Run` only -- publish refreshes Neon from the Sheet and never sends a notification, so a chat id there is dead weight. Update the Phase 6 security test so exactly those steps may see them.
5. **Dashboard labels.** In Vercel set `DASH_PROFILE_LABELS=support=Customer support,community=Community and programs` (no `NEXT_PUBLIC_` prefix).
6. **Local runs.** Add the same two names to `.env` and `.env.example`.

## Database migration
Run `migrations/003_profile.sql` on the Neon `dev` branch, then production, with the direct connection string. It backfills existing rows to profile `support`. If your first profile id is not `support`, change both marked `(A)` lines first. Apply it to the local `jobs` and `jobs_test` databases too. The existing `tests/test_neon_integration.py` was not reviewed and must be updated for the new `replace_jobs(profile=...)` and `count_jobs(profile)` signatures.

## Dashboard without a login
You chose no auth. What that means:
- Anyone with the Vercel URL can read both people's listings, scores and `application_status`, and can switch profile or edit `?profile=`. The switcher is a view, not a boundary.
- It conflicts with doc 03 (listings are not to be republished publicly) and with D24, which existed for that reason and to stop bots waking Neon.
- Only ids and statuses are visible. Notes, dates and personal columns are still not pushed (D20).

Cheap steps that keep the open design: keep `X-Robots-Tag: noindex` and the disallow-all `robots.txt`; keep the 60-second cache; do not share the URL. Two options you can take later: stop publishing `application_status` (drops the status filter), or serve each profile under an unguessable path. Both are small changes.

### Edits to the pages (not seen, so described)
- `app/page.tsx`: `const profiles = await listProfiles(); const profile = resolveProfile(searchParams.profile, profiles);` If `profile` is null, show "No data published yet". Pass `profile` to `listJobs(filters, profile)`, `overview(profile)` and `filterOptions(profile)`. Render `<ProfileSwitcher profiles={profiles} current={profile} />` above the filters.
- Filter form, pagination and job cards must carry `profile` (a hidden input, and `&profile=` in links), or paging would jump back to the first profile.
- `app/jobs/[id]/page.tsx`: resolve the profile the same way, call `getJob(id, profile)`, and make the back link `/?profile=...`.
- `lib/db.ts`, `lib/filters.ts` need no change. `Filters` does not carry the profile on purpose: it is validated separately by `resolveProfile`.
- The SQL test lives at `frontend/tests/tests-profile-sql.test.ts` with corrected imports.

## Files in this drop
| File | Status |
|---|---|
| `src/jobscraper/profiles.py`, `cli.py`, `publish.py`, `publish_cli.py`, `storage/neon.py` | Complete files |
| `migrations/003_profile.sql` | New |
| `config/profiles.yaml`, `config/profiles/community/{profile,scoring}.yaml` | New. Your own `config/profile.yaml` and `scoring.yaml` stay where they are |
| `frontend/lib/{sql,queries,profiles}.ts`, `components/ProfileSwitcher.tsx` | Complete files |
| `tests/test_profiles.py`, `test_publish_profiles.py`, `test_skill_guards.py`, frontend SQL test | New |
| _(no patch file)_ | The patches described in earlier drafts were applied directly to the files above |

## What is verified, and what is not
| Checked here | How |
|---|---|
| Profile loader, including every refusal case and legacy fallback | Run with a stand-in for `ConfigError` |
| Publish loop: separate profiles, guard blocks only the affected one, unreadable Sheet never prunes, partial publish never prunes | Run with a stand-in for pydantic and a fake Neon |
| Second profile's YAML: no unknown keys, every skill in the dictionary, every regex compiles, region, title, scam and keyword patterns behave on sample strings | Run |
| Your own two real YAML files still contain only valid keys | Checked by hand against the model fields |

| Not run | Why |
|---|---|
| `cli.py` (full run, publish, recover) | Rewritten from the text you shared. No project code, pydantic, pytest or network here |
| `neon.py` against Postgres, and `003_profile.sql` | No Postgres and no psycopg here. Run the migration on `jobs_test` first |
| Frontend | Not installed or built. Pinned versions still unconfirmed (O10) |
| `test_skill_guards.py` | Depends on `skills.py`, which I have not seen. It may fail, and that failure is information |

Run `ruff format . && ruff check --fix . && mypy src && pytest`. Then prove nothing changed for you: with `config/profiles.yaml` deleted, a `run --dry-run --no-notify` must produce the same digest as before.

## Deferred
- **Years-of-experience cap, diploma deduction, watchlist-company boost** from the second profile's original file. None is wired, so the blocks were removed rather than left to look active. The cap and deduction fit inside the existing 10-point experience factor. The watchlist is better shown as a flag than as points.
- **First-run flood.** A new profile sees every current listing as new. `select_jobs` caps the first digest at 30 jobs (three messages), and later runs are normal. A `--seed` run that stores and marks everything as notified would avoid it.
- **More sources for this profile.** Jobicy is one request an hour for everyone, so it cannot be tuned per profile. We Work Remotely is now widened for this profile only: `config/profiles.yaml` gives it `sources: [himalayas, jobicy, weworkremotely, weworkremotely_categories]`, where naming `weworkremotely` also shares the support feed's single request, while the support profile stays on the single-support-feed `weworkremotely` id. Many watchlist companies use Lever or Ashby, which have no adapter yet.
- **Sheets read quota.** Each profile re-reads whole tabs several times per run. Check the per-minute quota (verify) before adding a third person.

## Not changed, and why
- `matching/skills.py`, `explain.py`: not seen. After the first dry run, run `python main.py brief <id> --for community` on a few jobs and look for customer-support wording or Zendesk-style advice. If it appears, send me `explain.py`.
- `postgres.py`: I could not run it, and from reading it I don't think it works against real rows (strings inserted into date, array and JSON columns; a failed insert inside a transaction before an update). It also shares the `jobs` database with the Neon schema. I'd delete it and use SQLite locally.
- `names.py` and `classify_location`: still Kenya-centred. Right for both profiles today. A person based elsewhere would need a `home` block (country, city, regions, timezone), which is the main piece of work this design deliberately leaves out.

## Rollout
1. Run lint, types and tests.
2. Dry run with `profiles.yaml` deleted and confirm your output is unchanged.
3. Restore `profiles.yaml` (community still `enabled: false`) and dry run again: still unchanged.
4. Run `003_profile.sql` on local `jobs_test`, update the integration tests, then on Neon `dev`.
5. `python main.py publish --dry-run`, then publish to `dev` twice. Compare a few rows with the Sheet.
6. Update the dashboard pages. Check the list, detail and paging all stay on the chosen profile.
7. Production: migrate, add the GitHub secrets and workflow env, watch three scheduled runs.
8. Second person's Sheet, secrets and chat. Set `enabled: true`. Run `python main.py run --only community --no-notify` first, then label about 30 jobs with `calibrate --for community` and aim for 80% agreement before the first real digest.
