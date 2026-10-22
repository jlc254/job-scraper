import { describe, expect, it } from "vitest";
import { withProfile } from "../lib/profile-links";

describe("withProfile", () => {
  it("adds profile to an href with no query string", () => {
    expect(withProfile("/", "community")).toBe("/?profile=community");
    expect(withProfile("/jobs/abc", "community")).toBe("/jobs/abc?profile=community");
  });

  it("appends profile to an existing query string", () => {
    expect(withProfile("/?tier=top", "community")).toBe("/?tier=top&profile=community");
  });

  it("replaces a profile that is already there", () => {
    const href = withProfile("/?profile=support&tier=top", "community");
    expect(href).toContain("profile=community");
    expect(href).not.toContain("profile=support");
    expect(href).toContain("tier=top");
  });

  it("keeps a hash at the end", () => {
    expect(withProfile("/?tier=top#jobs", "community")).toBe("/?tier=top&profile=community#jobs");
  });

  it("encodes the profile value", () => {
    expect(withProfile("/", "a b&c")).toBe("/?profile=a+b%26c");
  });

  it("never touches an external URL", () => {
    const external = "https://boards.example.com/apply?role=1";
    expect(withProfile(external, "community")).toBe(external);
    const protocolRelative = "//example.com/x";
    expect(withProfile(protocolRelative, "community")).toBe(protocolRelative);
  });
});
