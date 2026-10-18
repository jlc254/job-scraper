import { describe, expect, it } from "vitest";
import { buildListQuery } from "../lib/sql";
import type { Filters } from "../lib/filters";

const base = { tiers: ["top"], q: "", minScore: 0, page: 1, sort: "score" } as unknown as Filters;

describe("profile scoping", () => {
  it("always binds the profile as the first parameter, never inlines it", () => {
    const q = buildListQuery(base, "community");
    expect(q.params[0]).toBe("community");
    expect(q.countParams[0]).toBe("community");
    expect(q.text).toMatch(/WHERE profile = \$1/);
    expect(q.text).not.toContain("community");
  });

  it("a hostile profile value is a bound parameter, not SQL", () => {
    const q = buildListQuery(base, "x'; DROP TABLE jobs;--");
    expect(q.text).not.toMatch(/DROP/i);
    expect(q.params[0]).toBe("x'; DROP TABLE jobs;--");
  });
});
