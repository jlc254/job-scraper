export const TIERS = ["top", "strong", "potential", "weak"] as const;
export type Tier = (typeof TIERS)[number];
export const DEFAULT_TIERS: Tier[] = ["top", "strong", "potential"];

export const SORTS = ["score", "newest", "oldest", "deadline"] as const;
export type Sort = (typeof SORTS)[number];

export const WORK_TYPES = ["remote", "hybrid", "onsite", "unknown"] as const;
export const FOUND_OPTIONS = [1, 7, 30] as const;

export const PAGE_SIZE = 25;
export const MAX_LIMIT = 50;
const MAX_PAGE = 10_000;

export type RawParams = Record<string, string | string[] | undefined>;

export interface Filters {
  q?: string;
  tiers: Tier[];
  minScore: number;
  source?: string;
  workType?: string;
  eligibility?: string;
  employmentType?: string;
  status?: string;
  foundDays?: number;
  skill?: string;
  sort: Sort;
  page: number;
}

export function clamp(n: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, n));
}

export function clampLimit(n: number): number {
  if (!Number.isFinite(n)) return PAGE_SIZE;
  return clamp(Math.trunc(n), 1, MAX_LIMIT);
}

function first(v: string | string[] | undefined): string | undefined {
  return Array.isArray(v) ? v[0] : v;
}

function text(v: string | string[] | undefined, max = 80): string | undefined {
  const s = first(v)?.trim();
  return s ? s.slice(0, max) : undefined;
}

function int(v: string | string[] | undefined): number | undefined {
  const s = first(v)?.trim();
  if (s === undefined || !/^-?\d+(\.\d+)?$/.test(s)) return undefined;
  return Math.trunc(Number(s));
}

function parseTiers(v: string | string[] | undefined): Tier[] {
  const parts = (Array.isArray(v) ? v : v === undefined ? [] : [v])
    .flatMap((s) => s.split(","))
    .map((s) => s.trim().toLowerCase());
  const valid = TIERS.filter((t) => parts.includes(t));
  return valid.length ? [...valid] : [...DEFAULT_TIERS];
}

/** Turns untrusted URL parameters into a safe Filters object. Unknown keys are ignored. */
export function parseFilters(p: RawParams): Filters {
  const sortRaw = first(p.sort);
  const workRaw = first(p.work_type)?.toLowerCase();
  const found = int(p.found);
  return {
    q: text(p.q, 120),
    tiers: parseTiers(p.tier),
    minScore: clamp(int(p.min_score) ?? 0, 0, 100),
    source: text(p.source),
    workType: WORK_TYPES.includes(workRaw as (typeof WORK_TYPES)[number]) ? workRaw : undefined,
    eligibility: text(p.eligibility),
    employmentType: text(p.employment_type),
    status: text(p.status),
    foundDays: FOUND_OPTIONS.includes(found as (typeof FOUND_OPTIONS)[number]) ? found : undefined,
    skill: text(p.skill)?.toLowerCase(),
    sort: SORTS.includes(sortRaw as Sort) ? (sortRaw as Sort) : "score",
    page: clamp(int(p.page) ?? 1, 1, MAX_PAGE),
  };
}

function sameTiers(a: Tier[]): boolean {
  return a.length === DEFAULT_TIERS.length && DEFAULT_TIERS.every((t) => a.includes(t));
}

/** Builds a query string containing only non-default values. */
export function toQueryString(f: Filters, overrides: Partial<Filters> = {}): string {
  const m = { ...f, ...overrides };
  const sp = new URLSearchParams();
  if (m.q) sp.set("q", m.q);
  if (!sameTiers(m.tiers)) sp.set("tier", m.tiers.join(","));
  if (m.minScore > 0) sp.set("min_score", String(m.minScore));
  if (m.source) sp.set("source", m.source);
  if (m.workType) sp.set("work_type", m.workType);
  if (m.eligibility) sp.set("eligibility", m.eligibility);
  if (m.employmentType) sp.set("employment_type", m.employmentType);
  if (m.status) sp.set("status", m.status);
  if (m.foundDays) sp.set("found", String(m.foundDays));
  if (m.skill) sp.set("skill", m.skill);
  if (m.sort !== "score") sp.set("sort", m.sort);
  if (m.page > 1) sp.set("page", String(m.page));
  return sp.toString();
}

/** Parses the `back` parameter of the detail page into a clean query string. */
export function sanitizeBack(back: string | string[] | undefined): string {
  const raw = first(back);
  if (!raw || raw.length > 600) return "";
  const parsed = parseFilters(Object.fromEntries(new URLSearchParams(raw)));
  return toQueryString(parsed);
}

/** Number of non-default filters, shown on the mobile "Filters" button. */
export function activeFilterCount(f: Filters): number {
  return [
    f.q,
    !sameTiers(f.tiers) ? "tier" : undefined,
    f.minScore > 0 ? "min" : undefined,
    f.source,
    f.workType,
    f.eligibility,
    f.employmentType,
    f.status,
    f.foundDays,
    f.skill,
    f.sort !== "score" ? "sort" : undefined,
  ].filter((v) => v !== undefined && v !== "").length;
}
