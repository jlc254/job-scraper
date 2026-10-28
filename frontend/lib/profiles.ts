import { unstable_cache } from "next/cache";
import { query } from "./db";

export interface ProfileInfo {
  id: string;
  label: string;
  publishedAt: string | null;
}

/** Display names come from the server-only env var DASH_PROFILE_LABELS, for example
 *  "support=Customer support,community=Community and programs". Ids missing from it show as the id.
 *  Neon stores ids only: labels are presentation and can change without a migration. */
function labelMap(): Map<string, string> {
  const map = new Map<string, string>();
  for (const part of (process.env.DASH_PROFILE_LABELS ?? "").split(",")) {
    const [id, ...rest] = part.split("=");
    if (id?.trim() && rest.length) map.set(id.trim(), rest.join("=").trim());
  }
  return map;
}

async function loadProfiles(): Promise<ProfileInfo[]> {
  const rows = await query<{ profile: string; published_at: string | null }>(
    `SELECT profile,
            to_char(published_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') AS published_at
       FROM publish_meta ORDER BY profile`,
  );
  const labels = labelMap();
  return rows.map((r) => ({
    id: r.profile,
    label: labels.get(r.profile) ?? r.profile,
    publishedAt: r.published_at,
  }));
}

/** Profiles that have been published. Cached briefly to spare free-tier compute. */
export const listProfiles = unstable_cache(loadProfiles, ["profiles"], { revalidate: 60 });

/** Old profile ids that were renamed to persona ids. Kept so legacy links/bookmarks
 *  (e.g. ?profile=support) still land on the right persona instead of the default. */
const PROFILE_ALIASES: Record<string, string> = {
  support: "juliet",
  community: "jumalaw98",
};

/** The only way a profile id reaches a query: it must be one of the published profiles.
 *  An unknown or missing value falls back to the operator's profile (juliet by default,
 *  override with DASH_DEFAULT_PROFILE), never to "all profiles". Legacy alias values in
 *  DASH_DEFAULT_PROFILE (e.g. "community") are resolved to their persona id. */
const rawDefaultProfile = (process.env.DASH_DEFAULT_PROFILE ?? "").trim();
const DEFAULT_PROFILE = PROFILE_ALIASES[rawDefaultProfile] ?? (rawDefaultProfile || "juliet");

export function resolveProfile(param: string | string[] | undefined, available: ProfileInfo[]): string | null {
  const wanted = Array.isArray(param) ? param[0] : param;
  const resolved = wanted ? (PROFILE_ALIASES[wanted] ?? wanted) : wanted;
  if (resolved && available.some((p) => p.id === resolved)) return resolved;
  if (available.some((p) => p.id === DEFAULT_PROFILE)) return DEFAULT_PROFILE;
  return available[0]?.id ?? null;
}
