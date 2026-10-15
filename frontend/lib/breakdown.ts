export const FACTOR_ORDER = ["title", "skills", "location", "experience", "salary", "freshness", "industry"];

const LABELS: Record<string, string> = {
  title: "Title relevance",
  skills: "Skills overlap",
  location: "Location and eligibility",
  experience: "Experience level",
  salary: "Salary",
  freshness: "Freshness",
  industry: "Industry",
};

export interface Factor {
  key: string;
  label: string;
  points: number;
  max: number;
  reason: string;
}

export interface ParsedBreakdown {
  version: number | null;
  total: number | null;
  tier: string | null;
  factors: Factor[];
  flags: string[];
  skills: { required: string[]; preferred: string[]; matched: string[]; partial: string[]; missing: string[] };
}

const isObj = (v: unknown): v is Record<string, unknown> =>
  typeof v === "object" && v !== null && !Array.isArray(v);

function num(v: unknown): number | null {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string" && v.trim() !== "" && Number.isFinite(Number(v))) return Number(v);
  return null;
}

function strList(v: unknown): string[] {
  return Array.isArray(v)
    ? v.filter((x): x is string => typeof x === "string").map((x) => x.trim()).filter(Boolean)
    : [];
}

function factorFrom(key: string, f: unknown): Factor | null {
  if (!isObj(f)) return null;
  const label = (Object.prototype.hasOwnProperty.call(LABELS, key) ? LABELS[key] : key.replace(/_/g, " ")) ?? key;
  return {
    key,
    label,
    points: num(f.points) ?? 0,
    max: num(f.max) ?? 0,
    reason: typeof f.reason === "string" ? f.reason : "",
  };
}

/** Defensive parser: missing, null, malformed or partial breakdowns never throw. */
export function parseBreakdown(raw: unknown): ParsedBreakdown | null {
  let value = raw;
  if (typeof raw === "string") {
    try {
      value = JSON.parse(raw);
    } catch {
      return null;
    }
  }
  if (!isObj(value)) return null;

  const factors: Factor[] = [];
  const rawFactors = value.factors;
  if (isObj(rawFactors)) {
    for (const [k, f] of Object.entries(rawFactors)) {
      const parsed = factorFrom(k, f);
      if (parsed) factors.push(parsed);
    }
  } else if (Array.isArray(rawFactors)) {
    for (const f of rawFactors) {
      if (!isObj(f)) continue;
      const key = typeof f.key === "string" ? f.key : typeof f.name === "string" ? f.name : "";
      const parsed = key ? factorFrom(key, f) : null;
      if (parsed) factors.push(parsed);
    }
  }
  const rank = (k: string) => {
    const i = FACTOR_ORDER.indexOf(k);
    return i < 0 ? 99 : i;
  };
  factors.sort((a, b) => rank(a.key) - rank(b.key));

  const s = isObj(value.skills) ? value.skills : {};
  return {
    version: num(value.version),
    total: num(value.total),
    tier: typeof value.tier === "string" ? value.tier : null,
    factors,
    flags: strList(value.flags),
    skills: {
      required: strList(s.required),
      preferred: strList(s.preferred),
      matched: strList(s.matched),
      partial: strList(s.partial),
      missing: strList(s.missing),
    },
  };
}
