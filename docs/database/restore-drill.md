# Restore drill — first PITR restore of `neondb`

- **Drill branch:** `drill/2026-11-02` (`br-muddy-water-b5yy3rz4`)
- **Source:** PITR snapshot `drill-pitr-2026-11-02` (`snap-lively-shape-b5oak5rp`)
- **Executed:** 2026-11-02, 12:53–12:54 UTC
- **Status:** restore verified; teardown still pending (see
  [Cleanup blocked](#cleanup-blocked-outstanding-production-binding))

## Preconditions measured at run time

| Fact | Value at drill time |
| --- | --- |
| PITR / history retention | 6 h (21 600 s) |
| Branches before drill | `main`, archived `vercel-dev`, four `preview/dependabot/*` |
| Snapshots before drill | none |
| Restore point chosen | `2026-11-02T11:53:51Z` (≈1 h before the drill, inside the 6 h window) |

The restore timestamp was computed at run time, not copied from the plan: a
literal written into a plan is stale before the first run, because the Free
tier only keeps six hours of history.

## Commands

No `neonctl` binary and no `NEON_API_KEY` exist in the working environment, so
the same operations were issued through the Neon control-plane API via the MCP
server. The `neonctl` equivalents are shown alongside for reproducibility.

```bash
# 1. Compute the restore point at run time
TS=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)      # -> 2026-11-02T11:53:51Z

# 2. Create a PITR snapshot at that instant
#    neonctl snapshots create --name drill-pitr-2026-11-02 --timestamp "$TS"
#    API: create_snapshot { branch_id: main, timestamp: "$TS", name: "drill-pitr-2026-11-02" }

# 3. Restore the snapshot onto a throwaway branch
#    neonctl branches create --name drill/2026-11-02 --snapshot <snapshot-id>
#    API: restore_snapshot { snapshot_id, name: "drill/2026-11-02" }
```

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

## Data verification (read-only)

Executed twice, as `jobs_reader`, against the drill branch:

```sql
SELECT j.profile, count(*) AS live, m.job_count AS recorded
FROM jobs j JOIN publish_meta m USING (profile)
GROUP BY j.profile, m.job_count ORDER BY 1;

SELECT max(published_at) FROM publish_meta;
```

| Profile | live | recorded |
| --- | --- | --- |
| `juliet` | 137 | 137 |
| `jumalaw98` | 32 | 32 |

`max(published_at)` = `2026-11-02T10:54:14.908Z` — at or before the restore
point, as required.

Both runs returned **byte-identical output**, which is the proof that the drill
performed no writes: a write-capable role would have moved the counts between
the two reads. The restored point is a *coherent earlier moment*; it is not
claimed to equal today's live counts, which move on every publish.

## `finalize` — what went wrong, and why it matters

`restore_snapshot` defaults to `finalize: true`. Finalizing does not just create
a branch: it **reassigns the original branch's computes to the restored
branch**, which silently moved the production read-write endpoint
(`ep-ancient-waterfall-b55wkxu3`) onto `drill/2026-11-02` and left `main` with a
freshly created, unused endpoint (`ep-lingering-dawn-b57024s9`).

Consequences, all observed directly:

- `main` (`br-green-butterfly-b5opvq53`) now has no application traffic; the
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

**Rule for every future drill:** pass `finalize: false` when restoring onto a
throwaway branch, or deliberately call `finalize_branch_restore` only when the
intent is to promote the restored branch. The destructive default is the whole
reason this drill left production reading from a snapshot copy.

Data loss risk is currently nil because the dashboard is read-only and no
publish has run since the restore point — both branches still hold the same
rows and the same `max(published_at)`. That changes at the next scheduled
publish (`daily.yml`, 03:07 and 13:07 UTC), which writes through the endpoint
that is now bound to the drill branch.

## Cleanup (blocked — outstanding production binding)

Teardown is intentionally **not** done yet, in this order:

1. Human: set the Vercel → Neon integration **Production Branch** to `main`.
2. `update_postgres_endpoint` → move `ep-ancient-waterfall-b55wkxu3` back to
   `main`; delete the unused `ep-lingering-dawn-b57024s9`.
3. `delete_branch drill/2026-11-02`; `delete_snapshot drill-pitr-2026-11-02`.
4. Only then create the single Free-tier baseline snapshot
   (`baseline-2026-11-02`) — the one manual-snapshot slot is currently held by
   the drill snapshot.

## Repeat cadence

Repeat quarterly. Next due: **2027-02-02**, with `finalize: false`.
