import type { ParsedBreakdown } from "@/lib/breakdown";

/**
 * One bar for the whole 0 to 100 scale. Each segment is one scoring factor, drawn at its real
 * number of points, so the shape of the bar shows where the score came from. Decorative: the
 * numbers and reasons are always printed elsewhere.
 */
export default function ScoreBar({ breakdown, score }: { breakdown: ParsedBreakdown | null; score: number | null }) {
  const factors = breakdown?.factors.filter((f) => f.points > 0) ?? [];
  const title = factors.length ? factors.map((f) => `${f.label} ${f.points}`).join(", ") : "No breakdown stored";
  return (
    <div className="scorebar" aria-hidden="true" title={title}>
      {factors.length > 0 ? (
        factors.map((f, i) => (
          <span key={f.key} className={`seg seg-${i % 7}`} style={{ width: `${Math.min(100, f.points)}%` }} />
        ))
      ) : score ? (
        <span className="seg seg-0" style={{ width: `${Math.min(100, score)}%` }} />
      ) : null}
    </div>
  );
}
