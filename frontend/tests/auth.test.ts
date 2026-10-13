import { describe, expect, it } from "vitest";
import { checkBasicAuth, safeEqual } from "../lib/auth";

const basic = (s: string) => `Basic ${Buffer.from(s).toString("base64")}`;

describe("checkBasicAuth", () => {
  it("denies everyone when env vars are missing (fails closed)", () => {
    expect(checkBasicAuth(basic("a:b"), undefined, undefined)).toBe(false);
    expect(checkBasicAuth(basic(":"), "", "")).toBe(false);
    expect(checkBasicAuth(basic("a:b"), "a", undefined)).toBe(false);
  });
  it("denies wrong or missing credentials", () => {
    expect(checkBasicAuth(null, "a", "b")).toBe(false);
    expect(checkBasicAuth(basic("a:wrong"), "a", "b")).toBe(false);
    expect(checkBasicAuth(basic("x:b"), "a", "b")).toBe(false);
    expect(checkBasicAuth("Bearer abc", "a", "b")).toBe(false);
    expect(checkBasicAuth("Basic !!!notbase64", "a", "b")).toBe(false);
    expect(checkBasicAuth(basic("nocolon"), "a", "b")).toBe(false);
  });
  it("allows correct credentials, including a colon or non-ASCII in the password", () => {
    expect(checkBasicAuth(basic("a:b"), "a", "b")).toBe(true);
    expect(checkBasicAuth(basic("a:p:w"), "a", "p:w")).toBe(true);
    expect(checkBasicAuth(basic("a:pässwörd"), "a", "pässwörd")).toBe(true);
  });
});

describe("safeEqual", () => {
  it("compares strings", () => {
    expect(safeEqual("abc", "abc")).toBe(true);
    expect(safeEqual("abc", "abd")).toBe(false);
    expect(safeEqual("abc", "abcd")).toBe(false);
    expect(safeEqual(undefined, "a")).toBe(false);
  });
});
