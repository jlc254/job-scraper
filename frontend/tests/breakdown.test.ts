import { describe, expect, it } from "vitest";
import { parseBreakdown } from "../lib/breakdown";

describe("parseBreakdown", () => {
  it("returns null for missing or invalid input", () => {
    expect(parseBreakdown(null)).toBeNull();
    expect(parseBreakdown(undefined)).toBeNull();
    expect(parseBreakdown("not json")).toBeNull();
    expect(parseBreakdown([1, 2])).toBeNull();
  });
  it("parses a full breakdown and orders factors", () => {
    const b = parseBreakdown({
      version: 2,
      total: "85.5",
      tier: "top",
      factors: {
        skills: { points: 17.5, max: 25, reason: "7 of 10" },
        title: { points: 25, max: 25, reason: "Strong-list exact" },
      },
      flags: ["eligibility unconfirmed", 5],
      skills: { matched: ["zendesk"], missing: ["freshdesk"], partial: [] },
    });
    expect(b?.total).toBe(85.5);
    expect(b?.version).toBe(2);
    expect(b?.factors.map((f) => f.key)).toEqual(["title", "skills"]);
    expect(b?.flags).toEqual(["eligibility unconfirmed"]);
    expect(b?.skills.matched).toEqual(["zendesk"]);
  });
  it("survives partial data", () => {
    const b = parseBreakdown({ factors: { title: { points: "x" }, bad: 5 } });
    expect(b?.factors).toHaveLength(1);
    expect(b?.factors[0]?.points).toBe(0);
    expect(b?.skills.missing).toEqual([]);
  });
  it("accepts a JSON string", () => {
    expect(parseBreakdown('{"total": 62.4}')?.total).toBe(62.4);
  });
});
