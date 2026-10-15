import type { ParsedBreakdown } from "@/lib/breakdown";
import { formatScore } from "@/lib/format";

const fmt = (n: number): string => (Number.isInteger(n) ? String(n) : n.toFixed(1));

export default function ScoreBreakdown({ breakdown, score }: { breakdown: ParsedBreakdown; score: number | null }) {
  const sum = breakdown.factors.reduce((a, f) => a + f.points, 0);
  const total = breakdown.total ?? score ?? (breakdown.factors.length > 0 ? sum : null);

  return (
    <div>
      {breakdown.factors.length > 0 ? (
        <ul className="factors">
          {breakdown.factors.map((f) => {
            const pct = f.max > 0 ? Math.min(100, Math.max(0, (f.points / f.max) * 100)) : 0;
            return (
              <li key={f.key} className="factor">
                <div className="factor-head">
                  <span className="factor-label">{f.label}</span>
                  <span className="factor-points">
                    {fmt(f.points)} of {fmt(f.max)}
                  </span>
                </div>
                <div className="bar" aria-hidden="true">
                  <div className="bar-fill" style={{ width: `${pct}%` }} />
                </div>
                {f.reason ? <p className="factor-reason">{f.reason}</p> : null}
              </li>
            );
          })}
        </ul>
      ) : (
        <p className="muted">No factor breakdown was stored for this job.</p>
      )}
      {total !== null || breakdown.version !== null ? (
        <p className="factor-total">
          {total !== null ? `Total ${formatScore(total)} out of 100` : ""}
          {breakdown.version !== null
            ? `${total !== null ? ", " : ""}scoring version ${breakdown.version}`
            : ""}
        </p>
      ) : null}
      {breakdown.flags.length > 0 ? (
        <ul className="chips flags">
          {breakdown.flags.map((flag) => (
            <li key={flag} className="chip chip-flag">
              {flag}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
