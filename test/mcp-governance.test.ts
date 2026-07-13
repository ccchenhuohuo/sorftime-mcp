import { describe, expect, it } from "vitest";
import { ENDPOINT_GOVERNANCE, validateGovernanceCatalog } from "../src/core/governance.js";
import { ENDPOINTS } from "../src/endpoints.js";

describe("MCP endpoint governance", () => {
  it("classifies all 52 endpoints exactly once", () => {
    expect(() => validateGovernanceCatalog()).not.toThrow();
    expect(Object.keys(ENDPOINT_GOVERNANCE)).toHaveLength(52);
    expect(new Set(ENDPOINTS.map((endpoint) => endpoint.name))).toEqual(new Set(Object.keys(ENDPOINT_GOVERNANCE)));
  });

  it("only exposes endpoints that are both free and read-only", () => {
    const exposed = Object.entries(ENDPOINT_GOVERNANCE).filter(([, policy]) => policy.exposure !== "disabled");
    expect(exposed.length).toBeGreaterThan(0);
    for (const [, policy] of exposed) {
      expect(policy.billing).toBe("free");
      expect(policy.effect).toBe("read");
    }
    for (const name of ["ProductRequest", "ProductQuery", "CategoryAssistant", "KeywordBatchSubscription", "BestSellerListDelete", "ASINSubscription"]) {
      expect(ENDPOINT_GOVERNANCE[name]?.exposure).toBe("disabled");
    }
  });
});
