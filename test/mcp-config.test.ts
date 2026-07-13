import { describe, expect, it } from "vitest";
import { loadMcpRuntimeConfig } from "../src/mcp/config.js";

const base = {
  NODE_ENV: "test",
  SORFTIME_ACCOUNT_SK: "sentinel-upstream-token",
  SORFTIME_BASE_URL: "http://127.0.0.1:9999/api/",
  MCP_AUDIT_LOG_PATH: "/tmp/sorftime-mcp-test-audit.jsonl",
};

describe("MCP runtime configuration", () => {
  it("loads secure local defaults without exposing the upstream token in public fields", async () => {
    const config = await loadMcpRuntimeConfig(base);
    expect(config.http.authMode).toBe("disabled");
    expect(config.stdioIdentity).toMatchObject({ role: "reader", authSource: "stdio_config" });
    expect(JSON.stringify({ http: config.http, governance: config.governance })).not.toContain("sentinel-upstream-token");
  });

  it("requires per-user key records for api_key auth", async () => {
    await expect(loadMcpRuntimeConfig({ ...base, MCP_AUTH_MODE: "api_key" })).rejects.toThrow(/requires at least one/u);
    const config = await loadMcpRuntimeConfig({
      ...base,
      MCP_AUTH_MODE: "api_key",
      MCP_API_KEYS_JSON: JSON.stringify([{ key: "a".repeat(32), subject: "alice@example.com", tenant: "team", role: "reader" }]),
    });
    expect(config.http.apiKeyIdentities[0]).toMatchObject({ subject: "alice@example.com", tenant: "team", role: "reader" });
  });

  it("fails closed for production without authentication", async () => {
    await expect(loadMcpRuntimeConfig({ ...base, NODE_ENV: "production", SORFTIME_BASE_URL: "https://standardapi.sorftime.com/api/" })).rejects.toThrow(/cannot disable authentication/u);
  });
});
