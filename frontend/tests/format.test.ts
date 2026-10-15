import { describe, expect, it } from "vitest";
import { deadlineNote, formatDate, formatDateTime, formatScore, relativeDay, safeHttpUrl, todayInNairobi } from "../lib/format";

describe("todayInNairobi", () => {
  it("rolls to the next day after 21:00 UTC", () => {
    expect(todayInNairobi(new Date("2026-10-10T20:59:00Z"))).toBe("2026-10-10");
    expect(todayInNairobi(new Date("2026-10-10T21:00:00Z"))).toBe("2026-10-11");
  });
});

describe("deadlineNote", () => {
  const today = "2026-10-10";
  it("labels past, today, tomorrow, soon and later", () => {
    expect(deadlineNote("2026-10-09", today)).toEqual({ text: "Closed", urgency: "closed" });
    expect(deadlineNote("2026-10-10", today)).toEqual({ text: "Closes today", urgency: "soon" });
    expect(deadlineNote("2026-10-11", today)).toEqual({ text: "Closes tomorrow", urgency: "soon" });
    expect(deadlineNote("2026-10-13", today)).toEqual({ text: "Closes in 3 days", urgency: "soon" });
    expect(deadlineNote("2026-10-20", today)).toEqual({ text: "Closes in 10 days", urgency: "normal" });
  });
  it("handles missing or malformed deadlines", () => {
    expect(deadlineNote(null, today).urgency).toBe("none");
    expect(deadlineNote("soon", today).urgency).toBe("none");
  });
});

describe("safeHttpUrl", () => {
  it("allows only absolute http(s) links", () => {
    expect(safeHttpUrl("https://example.com/job/1")).toBe("https://example.com/job/1");
    expect(safeHttpUrl("javascript:alert(1)")).toBeNull();
    expect(safeHttpUrl("/jobs/5")).toBeNull();
    expect(safeHttpUrl("data:text/html,x")).toBeNull();
    expect(safeHttpUrl(null)).toBeNull();
  });
});

describe("dates and scores", () => {
  it("formats without time-zone shifts", () => {
    expect(formatDate("2026-10-01")).toBe("1 Oct 2026");
    expect(relativeDay("2026-10-08", "2026-10-10")).toBe("2 days ago");
    expect(relativeDay("2026-10-09", "2026-10-10")).toBe("yesterday");
  });
  it("formats dateTime including year", () => {
    expect(formatDateTime("2026-10-01T08:30:00Z")).toContain("2026");
    expect(formatDateTime("2026-10-01T08:30:00Z")).toBe("1 Oct 2026, 11:30 EAT");
    expect(formatDateTime(null)).toBe("Unknown");
  });
  it("formats scores", () => {
    expect(formatScore(85.5)).toBe("85.5");
    expect(formatScore(90)).toBe("90");
    expect(formatScore(null)).toBe("–");
  });
});
