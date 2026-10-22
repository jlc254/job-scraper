import Link from "next/link";
import type { ProfileInfo } from "@/lib/profiles";

/** Server component, no client state. Switching resets the filters on purpose: skills, sources
 *  and statuses differ between people, so a filter from one profile would mean nothing in another.
 *  The current profile is marked with aria-current and text, not colour alone. */
export default function ProfileSwitcher({ profiles, current }: { profiles: ProfileInfo[]; current: string }) {
  if (profiles.length < 2) return null;
  return (
    <nav aria-label="Profile" style={{ display: "flex", gap: 8, flexWrap: "wrap", margin: "0 0 16px" }}>
      {profiles.map((p) => {
        const active = p.id === current;
        return (
          <Link
            key={p.id}
            href={`/?profile=${encodeURIComponent(p.id)}`}
            aria-current={active ? "page" : undefined}
            style={{
              padding: "6px 12px",
              borderRadius: 999,
              border: "1px solid currentColor",
              fontWeight: active ? 700 : 400,
              textDecoration: active ? "underline" : "none",
            }}
          >
            {p.label}
            {active ? " (viewing)" : ""}
          </Link>
        );
      })}
    </nav>
  );
}
