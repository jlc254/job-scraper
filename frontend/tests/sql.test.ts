import { describe, expect, it } from "vitest";
import { parseFilters } from "../lib/filters";
import { ORDER_BY, buildListQuery } from "../lib/sql";

const placeholders = (s: string) => new Set(s.match(/\$\d+/g) ?? []).size;

describe("buildListQuery", () => {
  it("binds hostile text as a parameter, never into the SQL", () => {
    const evil = "x'; DROP TABLE jobs; --";
    const q = buildListQuery(parseFilters({ q: evil, source: evil, skill: evil }));
    expect(q.text).not.toContain("DROP");
    expect(q.countText).not.toContain("DROP");
    expect(q.params).toContain(evil);
  });
  it("has one parameter per placeholder", () => {
    const q = buildListQuery(parseFilters({ q: "a", source: "b", min_score: "50", found: "7", skill: "excel", page: "2" }));
    expect(placeholders(q.text)).toBe(q.params.length);
    expect(placeholders(q.countText)).toBe(q.countParams.length);
  });
  it("defaults to hiding weak jobs", () => {
    const q = buildListQuery(parseFilters({}));
    expect(q.params[0]).toEqual(["top", "strong", "potential"]);
  });
  it("uses only allowlisted ORDER BY text", () => {
    for (const sort of ["score", "newest", "oldest", "deadline", "bogus"]) {
      const q = buildListQuery(parseFilters({ sort }));
      expect(Object.values(ORDER_BY).some((o) => q.text.includes(o))).toBe(true);
    }
  });
  it("computes the offset from the page", () => {
    const q = buildListQuery(parseFilters({ page: "3" }));
    expect(q.params.slice(-2)).toEqual([25, 50]);
  });
});
