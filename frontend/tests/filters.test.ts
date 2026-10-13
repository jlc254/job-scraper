import { describe, expect, it } from "vitest";
import { DEFAULT_TIERS, clampLimit, parseFilters, sanitizeBack, toQueryString } from "../lib/filters";

describe("parseFilters", () => {
  it("returns safe defaults", () => {
    const f = parseFilters({});
    expect(f.tiers).toEqual(DEFAULT_TIERS);
    expect(f.sort).toBe("score");
    expect(f.page).toBe(1);
    expect(f.minScore).toBe(0);
  });
  it("ignores unknown parameters", () => {
    expect(parseFilters({ evil: "1; DROP TABLE jobs" })).toEqual(parseFilters({}));
  });
  it("falls back when sort is outside the allowlist", () => {
    expect(parseFilters({ sort: "match_score; DROP" }).sort).toBe("score");
    expect(parseFilters({ sort: "deadline" }).sort).toBe("deadline");
  });
  it("clamps page and min_score", () => {
    expect(parseFilters({ page: "-4" }).page).toBe(1);
    expect(parseFilters({ page: "abc" }).page).toBe(1);
    expect(parseFilters({ page: "99999999" }).page).toBe(10_000);
    expect(parseFilters({ min_score: "250" }).minScore).toBe(100);
    expect(parseFilters({ min_score: "-5" }).minScore).toBe(0);
  });
  it("parses tiers from commas, repeats and junk", () => {
    expect(parseFilters({ tier: "top,weak" }).tiers).toEqual(["top", "weak"]);
    expect(parseFilters({ tier: ["strong", "potential"] }).tiers).toEqual(["strong", "potential"]);
    expect(parseFilters({ tier: "nonsense" }).tiers).toEqual(DEFAULT_TIERS);
  });
  it("accepts only listed work types and found windows", () => {
    expect(parseFilters({ work_type: "remote" }).workType).toBe("remote");
    expect(parseFilters({ work_type: "moon" }).workType).toBeUndefined();
    expect(parseFilters({ found: "7" }).foundDays).toBe(7);
    expect(parseFilters({ found: "9" }).foundDays).toBeUndefined();
  });
  it("lowercases skill and caps text length", () => {
    expect(parseFilters({ skill: "Zendesk" }).skill).toBe("zendesk");
    expect(parseFilters({ q: "x".repeat(500) }).q?.length).toBe(120);
  });
});

describe("clampLimit", () => {
  it("never exceeds 50", () => {
    expect(clampLimit(500)).toBe(50);
    expect(clampLimit(0)).toBe(1);
    expect(clampLimit(Number.NaN)).toBe(25);
  });
});

describe("toQueryString and sanitizeBack", () => {
  it("omits defaults and round-trips", () => {
    expect(toQueryString(parseFilters({}))).toBe("");
    const f = parseFilters({ q: "support", sort: "newest", page: "3", tier: "top" });
    expect(parseFilters(Object.fromEntries(new URLSearchParams(toQueryString(f))))).toEqual(f);
  });
  it("cleans a hostile back value", () => {
    expect(sanitizeBack("sort=hack&q=hi&x=1")).toBe("q=hi");
    expect(sanitizeBack("a".repeat(1000))).toBe("");
    expect(sanitizeBack(undefined)).toBe("");
  });
});
