import Link from "next/link";
import { formatDateTime, humanize, tierLabel } from "@/lib/format";
import type { Overview } from "@/lib/types";

const ORDER = ["top", "strong", "potential", "weak"] as const;
const STALE_HOURS = 36;

export default function OverviewStrip({ overview, shown }: { overview: Overview; shown: number }) {
  const segments = ORDER.map((t) => ({ tier: t, n: overview.tiers[t] ?? 0 })).filter((s) => s.n > 0);
  const stale =
    overview.publishedAt !== null && Date.now() - Date.parse(overview.publishedAt) > STALE_HOURS * 3_600_000;

  return (
    <section className="overview" aria-label="Overview">
      <p className="overview-line">
        <strong>{shown}</strong> {shown === 1 ? "job matches" : "jobs match"} these filters.{" "}
        <strong>{overview.new7d}</strong> found in the last 7 days.
      </p>

      {segments.length > 0 ? (
        <ul className="tierbar" aria-label="Jobs by tier">
          {segments.map((s) => (
            <li key={s.tier} style={{ flexGrow: s.n }} className={`tier-${s.tier}`}>
              <Link href={`/?tier=${s.tier}`}>
                {tierLabel(s.tier)} <span className="tierbar-n">{s.n}</span>
              </Link>
            </li>
          ))}
        </ul>
      ) : null}

      {overview.sources.length > 0 ? (
        <p className="sources">
          <span className="muted">By source</span>
          {overview.sources.map((s) => (
            <Link key={s.source} href={`/?source=${encodeURIComponent(s.source)}`} className="source-link">
              {humanize(s.source)} {s.n}
            </Link>
          ))}
        </p>
      ) : null}

      <p className="asof">
        {overview.publishedAt ? `Data as of ${formatDateTime(overview.publishedAt)}` : "No data published yet"}
      </p>
      {stale ? (
        <p className="stale" role="status">
          This data is more than {STALE_HOURS} hours old. Check the publish step in the GitHub Actions run.
        </p>
      ) : null}
    </section>
  );
}
