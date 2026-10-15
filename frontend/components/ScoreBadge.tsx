import { formatScore, tierLabel } from "@/lib/format";

export default function ScoreBadge({ score, tier, large = false }: { score: number | null; tier: string; large?: boolean }) {
  return (
    <div className={`score tier-${tier}${large ? " score-large" : ""}`}>
      <span className="score-num">{formatScore(score)}</span>
      <span className="score-tier">{tierLabel(tier)}</span>
    </div>
  );
}
