# Restore drill — first PITR restore of `neondb`

- **Drill branch:** `drill/2026-11-02` (`br-muddy-water-b5yy3rz4`)
- **Source:** PITR snapshot `drill-pitr-2026-11-02` (`snap-lively-shape-b5oak5rp`),
  source branch `main` (`br-green-butterfly-b5opvq53`)
- **Executed:** 2026-11-02, 12:53–12:54 UTC
- **Status:** restore verified. **Production is still bound to the drill branch
  and the branches have diverged**, so the client data is the blocker — see
  [Current state](#current-state--production-is-still-on-the-drill-branch) and
  [Cleanup](#cleanup-blocked--outstanding-production-binding).

## Preconditions measured at run time

| Fact | Value at drill time |
| --- | --- |
| PITR / history retention | 6 h (21 600 s) |
| Branches before drill | `main`, archived `vercel-dev`, four `preview/dependabot/*` |
| Snapshots before drill | none |
| Restore point chosen | `2026-11-02T11:53:51Z` (≈1 h before the drill, inside the 6 h window) |

The restore timestamp was computed at run time (`date -u -d '1 hour ago'`), not
copied from the plan: a literal written into a plan is stale before the first
run, because the Free tier only keeps six hours of history. The literal above is
a record of the value that was used, not a reusable one.

## What was executed

No `neonctl` binary and no `NEON_API_KEY` exist in the working environment, so
every operation went through the Neon control-plane API via the MCP server.
These are the calls that actually ran, with the identifiers they returned:

```text
create_snapshot({
  project_id: "autumn-rain-77812061",
  branch_id:  "br-green-butterfly-b5opvq53",       // main
  timestamp:  "2026-11-02T11:53:51Z",
  name:       "drill-pitr-2026-11-02",
})
→ id:               "snap-lively-shape-b5oak5rp"
  source_branch_id: "br-green-butterfly-b5opvq53"
  created_at:       "2026-11-02T12:53:59Z"
  manual:           true

restore_snapshot({
  project_id:  "autumn-rain-77812061",
  snapshot_id: "snap-lively-shape-b5oak5rp",
  // `finalize` omitted — see the next section; this is what caused the incident
})
→ id:             "br-muddy-water-b5yy3rz4"
  restore_status: "finalized"

rename_branch({ branch_id: "br-muddy-water-b5yy3rz4", name: "drill/2026-11-02" })
```

The branch was created with an auto-generated name and renamed afterwards, which
is why the id (`br-muddy-water-b5yy3rz4`) and the name (`drill/2026-11-02`) do
not correspond.

## Timing

| Event | Timestamp (UTC) | Elapsed |
| --- | --- | --- |
| Snapshot created | `2026-11-02T12:53:59Z` | — |
| Restore started | `2026-11-02T12:54:04.639Z` | — |
| Restore finished | `2026-11-02T12:54:06.634Z` | **1.995 s** |
| Second read finished | `2026-11-02T12:54:27Z` | — |

The 1.995 s figure is the control-plane time to make the restored branch
available (copy-on-write, no data copy). It is **not** an RTO: it excludes
repointing the application at the restored branch, redeploying, and any DNS or
environment-variable change. Task 18 must not treat this number as the whole
recovery time.

## `finalize` — what went wrong, and why it matters

The default is not what it appears to be at each layer:

- **Control-plane API:** `POST /projects/{project_id}/snapshots/{snapshot_id}/restore`
  takes `finalize_restore` in the body, documented with `"default": false`.
- **MCP wrapper:** `restore_snapshot` exposes `finalize`, documented as
  *"Defaults to true when restoring as a new branch and false when restoring
  onto an existing branch."*

The drill restored onto a **new** branch and omitted `finalize`, so the wrapper
sent `finalize_restore: true`. That is the exact argument that caused this
incident — not an un-finalized default.

Finalizing does not just create a branch: it **reassigns the original branch's
computes to the restored branch**. That silently moved the production
read-write endpoint (`ep-ancient-waterfall-b55wkxu3`) onto `drill/2026-11-02`
and left `main` with a freshly created, unused endpoint
(`ep-lingering-dawn-b57024s9`).

Consequences, all observed directly:

- `main` (`br-green-butterfly-b5opvq53`) has no application traffic; the
  dashboard's pooled `jobs_reader` sessions are all served by
  `drill/2026-11-02` (see [role-verification.md](role-verification.md)).
- `drill/2026-11-02` carries `restricted_actions`: `delete`,
  `delete-rw-endpoint`, `move-rw-endpoint-using-api`, each with the reason
  `vercel production branch`.
- The Neon API refuses to correct the binding while the restriction stands:

  ```
  HTTP 422  cannot move the read-write endpoint of a Vercel production branch;
            change the Vercel production branch first
  ```

  Only the Vercel integration's production-branch setting (dashboard) can lift
  it — no API or MCP surface exposes that setting.

**Rule for every future drill:** pass `finalize: false` explicitly when
restoring onto a throwaway branch, or deliberately call
`finalize_branch_restore` only when the intent is to promote the restored
branch. Relying on the default is unsafe because the MCP wrapper and the
control-plane API disagree about it.

## Data verification

Executed as `jobs_reader` against the drill branch. The join is a **FULL OUTER**
join on purpose: an inner join silently drops any profile that has no
`publish_meta` row and would report "all profiles match" while omitting it.

```sql
SELECT COALESCE(j.profile, m.profile) AS profile,
       count(j.job_id)                AS live,
       m.job_count                    AS recorded,
       m.published_at
FROM jobs j
FULL OUTER JOIN publish_meta m USING (profile)
GROUP BY COALESCE(j.profile, m.profile), m.job_count, m.published_at
ORDER BY 1;

SELECT max(published_at) FROM publish_meta;
```

A profile present in `jobs` but missing from `publish_meta` surfaces as
`recorded = null`; one present only in `publish_meta` surfaces as `live = 0`.

**At drill time (2026-11-02, 12:54 UTC):**

| Profile | live | recorded | `published_at` |
| --- | --- | --- | --- |
| `juliet` | 137 | 137 | `2026-11-02T10:54:14.908Z` |
| `jumalaw98` | 32 | 32 | `2026-11-02T10:54:14.908Z` |

`max(published_at)` was at or before the restore point, as required.

**Re-read on 2026-11-03 (same drill branch):**

| Profile | live | recorded | `published_at` |
| --- | --- | --- | --- |
| `juliet` | 95 | 95 | `2026-11-02T22:18:47.628Z` |
| `jumalaw98` | 32 | 32 | `2026-11-02T22:18:47.628Z` |

The counts moved because a publish ran after the drill, not because the drill
wrote anything — see the divergence section below. The restored point is a
*coherent earlier moment*; it is not claimed to equal today's live counts, which
move on every publish.

## Stability check, and why it is not proof of read-only

The two reads returned identical output at drill time. That is a **stability
check**: it shows no writes landed between the two reads, not that the
connection could not write. A write-capable role that performs only reads
produces the same result.

The read-only claim rests on the role itself, not on the reads:

- live `pg_roles`: `jobs_reader` has `rolcanlogin = true`, and
  `rolsuper`, `rolcreatedb`, `rolcreaterole` all `false`;
- `migrations/002_roles.sql` grants `SELECT` only on `jobs` and `publish_meta`
  and raises if the role is absent.

## Current state — production is still on the drill branch

Because production is bound to `drill/2026-11-02`, the scheduled
`daily-run` (03:07 and 13:07 UTC) writes **there**, not to `main`. That has
already happened once: run `41535980066` fired at `2026-11-02T22:17:28Z` and
published at `22:18:47Z` into the drill branch.

Verified on 2026-11-03, sampling each branch directly:

| Fact | `main` (`br-green-butterfly-b5opvq53`) | `drill/2026-11-02` (`br-muddy-water-b5yy3rz4`) |
| --- | --- | --- |
| `count(*) FROM jobs` | 169 | 127 |
| `publish_meta` | `juliet=137, jumalaw98=32` | `juliet=95, jumalaw98=32` |
| `max(published_at)` | `2026-11-02T10:54:14.908Z` | `2026-11-02T22:18:47.628Z` |
| Application traffic | none | all of it |

**The drill branch holds the newest publish; `main` is stale.** Deleting the
drill branch at this point would discard the `22:18:47Z` publish and leave the
dashboard reading the older `10:54:14Z` state. Teardown is therefore unsafe
until `main` is republished and verified.

## Cleanup (blocked — outstanding production binding)

Do these in order. Steps 1 and 2 are prerequisites, not ceremony: skipping
either destroys or strands data.

1. **Stop or redirect publishes first.** While the endpoint stays on
   `drill/2026-11-02`, every `daily-run` writes to a branch that step 5 deletes.
   Either disable the `daily.yml` schedule until the move is done, or accept
   that whatever lands there must be replayed into `main` afterwards.
2. **Human, in the Vercel UI:** Neon Console → project `autumn-rain-77812061` →
   Integrations → Vercel → Settings → **Production branch** = `main`. Then
   redeploy production in Vercel. This is the only way to lift the
   `vercel production branch` restriction; it is not in Vercel project settings
   and is not exposed by any API.
3. `update_postgres_endpoint` → move `ep-ancient-waterfall-b55wkxu3` back to
   `main`; delete the unused `ep-lingering-dawn-b57024s9`.
4. **Republish into `main`** — `workflow_dispatch` on `daily.yml` with
   `mode: publish` — and confirm `main`'s `publish_meta.max(published_at)` is at
   least `2026-11-02T22:18:47.628Z` before deleting anything.
5. `delete_branch drill/2026-11-02`; `delete_snapshot drill-pitr-2026-11-02`.
6. Only then create the single Free-tier baseline snapshot
   (`baseline-2026-11-02`); the one manual-snapshot slot is currently held by
   the drill snapshot.
7. Re-run the before/after role sample on `main` under load and record it in
   [role-verification.md](role-verification.md), closing the scope caveat there.

## Repeat cadence

Repeat quarterly. Next due: **2027-02-02**, with `finalize: false` passed
explicitly.
