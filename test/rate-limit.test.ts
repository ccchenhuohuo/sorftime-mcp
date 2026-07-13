import { describe, expect, it } from "vitest";
import { IdentityRateLimiter } from "../src/mcp/rate-limit.js";

describe("MCP identity rate limiter", () => {
  it("isolates identities and refills after one minute", () => {
    let now = 0;
    const limiter = new IdentityRateLimiter(2, 10, () => now);
    expect(limiter.take('["team","alice"]').allowed).toBe(true);
    expect(limiter.take('["team","alice"]').allowed).toBe(true);
    expect(limiter.take('["team","alice"]')).toMatchObject({ allowed: false, retryAfterSeconds: 60 });
    expect(limiter.take('["team","bob"]').allowed).toBe(true);
    now = 60_000;
    expect(limiter.take('["team","alice"]').allowed).toBe(true);
  });
});
