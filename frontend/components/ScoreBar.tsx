import type { ParsedBreakdown } from "@/lib/breakdown";
import { FACTOR_ORDER } from "@/lib/breakdown";

/**
 * One bar for the whole 0 to 100 scale. Each segment is one scoring factor, drawn at its real
 * number of points, so the shape of the bar shows where the score came from. Decorative: the
 * numbers and reasons are always printed elsewhere.
 */
export default function ScoreBar({ breakdown, score }: { breakdown: ParsedBreakdown | null; score: number | null }) {
  const allFactors = breakdown?.factors ?? [];
  const factors = allFactors.filter((f) => f.points > 0);
  const title = factors.length ? factors.map((f) => `${f.label} ${f.points}`).join(", ") : "No breakdown stored";
  return (
    <div className="scorebar" aria-hidden="true" title={title}>
      {factors.length > 0 ? (
        factors.map((f, i) => {
          const originalIndex = allFactors.indexOf(f);
          const segIndex = originalIndex >= 0 ? originalIndex : FACTOR_ORDER.indexOf(f.key);
          const colorIndex = segIndex >= 0 ? segIndex : i;
          return (
            <span key={f.key} className={`seg seg-${colorIndex % 7}`} style={{ width: `${Math.min(100, f.points)}%` }} />
          );
        })
      ) : score ? (
        <span className="seg seg-0" style={{ width: `${Math.min(100, score)}%` }} />
      ) : null}
    </div>
  );
}
