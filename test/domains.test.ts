import { describe, expect, it } from "vitest";
import { DOMAINS, resolveDomain } from "../src/domains.js";
import { ValidationError } from "../src/errors.js";

describe("domain registry", () => {
  it("contains the 14 documented marketplaces with stable IDs", () => {
    expect(DOMAINS.map(({ id, code }) => [id, code])).toEqual([
      [1, "US"],
      [2, "GB"],
      [3, "DE"],
      [4, "FR"],
      [5, "IN"],
      [6, "CA"],
      [7, "JP"],
      [8, "ES"],
      [9, "IT"],
      [10, "MX"],
      [11, "AE"],
      [12, "AU"],
      [13, "BR"],
      [14, "SA"],
    ]);
    expect(new Set(DOMAINS.map((domain) => domain.id)).size).toBe(14);
    expect(new Set(DOMAINS.map((domain) => domain.code)).size).toBe(14);
  });

  it("marks exactly the five marketplaces without history backfill", () => {
    expect(DOMAINS.filter((domain) => !domain.historyBackfill).map((domain) => domain.code).sort()).toEqual([
      "AE",
      "AU",
      "BR",
      "IN",
      "SA",
    ]);
  });

  it.each([
    [undefined, "US"],
    [1, "US"],
    ["1", "US"],
    [" us ", "US"],
    ["USA", "US"],
    ["uk", "GB"],
    ["英国", "GB"],
    ["uae", "AE"],
    ["KSA", "SA"],
    ["日本", "JP"],
  ] as const)("resolves %s to %s", (input, expectedCode) => {
    expect(resolveDomain(input).code).toBe(expectedCode);
  });

  it("rejects unknown IDs and aliases", () => {
    expect(() => resolveDomain(15)).toThrow(ValidationError);
    expect(() => resolveDomain("moon")).toThrow("Unsupported domain 'moon'");
  });
});
