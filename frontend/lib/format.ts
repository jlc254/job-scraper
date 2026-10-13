const TZ = "Africa/Nairobi";
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;

export function todayInNairobi(now: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: TZ,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(now);
}

function dayNumber(d: string): number {
  const [y, m, day] = d.split("-").map(Number) as [number, number, number];
  return Date.UTC(y, m - 1, day) / 86_400_000;
}

export function daysBetween(from: string, to: string): number {
  return dayNumber(to) - dayNumber(from);
}

export function isoToNairobiDate(iso: string): string {
  return todayInNairobi(new Date(iso));
}

/** Dates without a time (posted, deadline) are formatted as plain dates, never shifted by time zone. */
export function formatDate(d: string | null): string {
  if (!d || !DATE_RE.test(d)) return "Unknown";
  return new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${d}T00:00:00Z`));
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "Unknown";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Unknown";
  const s = new Intl.DateTimeFormat("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: TZ,
  }).format(date);
  return `${s} EAT`;
}

export function relativeDay(d: string | null, today: string): string {
  if (!d || !DATE_RE.test(d)) return "unknown";
  const n = daysBetween(d, today);
  if (n < 0) return formatDate(d);
  if (n === 0) return "today";
  if (n === 1) return "yesterday";
  return `${n} days ago`;
}

export type Urgency = "none" | "normal" | "soon" | "closed";

export function deadlineNote(deadline: string | null, today: string): { text: string; urgency: Urgency } {
  if (!deadline || !DATE_RE.test(deadline)) return { text: "", urgency: "none" };
  const n = daysBetween(today, deadline);
  if (n < 0) return { text: "Closed", urgency: "closed" };
  if (n === 0) return { text: "Closes today", urgency: "soon" };
  if (n === 1) return { text: "Closes tomorrow", urgency: "soon" };
  return { text: `Closes in ${n} days`, urgency: n <= 3 ? "soon" : "normal" };
}

/** Returns the URL only if it is an absolute http(s) link. Anything else is not rendered as a link. */
export function safeHttpUrl(url: string | null | undefined): string | null {
  if (!url || !/^https?:\/\//i.test(url)) return null;
  try {
    const u = new URL(url);
    return u.protocol === "http:" || u.protocol === "https:" ? u.toString() : null;
  } catch {
    return null;
  }
}

export function formatScore(n: number | null): string {
  if (n === null || !Number.isFinite(n)) return "–";
  return Number.isInteger(n) ? String(n) : n.toFixed(1);
}

const TIER_LABELS: Record<string, string> = {
  top: "Top",
  strong: "Strong",
  potential: "Potential",
  weak: "Weak",
  unscored: "Unscored",
};
export const tierLabel = (t: string) => TIER_LABELS[t] ?? t;

const ELIGIBILITY_LABELS: Record<string, string> = {
  worldwide: "Open worldwide",
  africa: "Open to Africa",
  east_africa: "Open to East Africa",
  kenya: "Open to Kenya",
  timezone_limited: "Timezone limited",
  restricted: "Restricted region",
  unclear: "Eligibility unconfirmed",
};
export const eligibilityLabel = (v: string) => ELIGIBILITY_LABELS[v] ?? v.replace(/_/g, " ");

const WORK_LABELS: Record<string, string> = {
  remote: "Remote",
  hybrid: "Hybrid",
  onsite: "On-site",
  unknown: "Work type unknown",
};
export const workTypeLabel = (v: string) => WORK_LABELS[v] ?? v;

export const humanize = (v: string) => {
  const s = v.replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
};
