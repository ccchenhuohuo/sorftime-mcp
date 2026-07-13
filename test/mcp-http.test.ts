import { once } from "node:events";
import { request as httpRequest } from "node:http";
import type { AddressInfo } from "node:net";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { describe, expect, it, vi } from "vitest";
import type { SorftimeCoreClient } from "../src/core/service.js";
import { MemoryAuditSink } from "../src/mcp/audit.js";
import { createMcpAppContext } from "../src/mcp/context.js";
import { startMcpHttpServer } from "../src/mcp/http-server.js";
import { IdentityRateLimiter } from "../src/mcp/rate-limit.js";

function getWithHost(url: string, host: string): Promise<number | undefined> {
  const target = new URL(url);
  return new Promise((resolve, reject) => {
    const request = httpRequest({
      hostname: target.hostname,
      port: target.port,
      path: target.pathname,
      method: "GET",
      headers: { host },
    }, (response) => {
      response.resume();
      response.once("end", () => resolve(response.statusCode));
    });
    request.once("error", reject);
    request.end();
  });
}

async function start(options: { auth?: boolean; origin?: string; allowedHosts?: string[]; maxSessions?: number } = {}) {
  const apiKey = "http-user-key-which-is-at-least-32-characters";
  const secondApiKey = "second-http-user-key-at-least-32-characters";
  const context = await createMcpAppContext({
    NODE_ENV: "test",
    SORFTIME_ACCOUNT_SK: "http-upstream-token-sentinel",
    SORFTIME_BASE_URL: "http://127.0.0.1:9999/api/",
    MCP_HTTP_PORT: "3001",
    MCP_AUTH_MODE: options.auth ? "api_key" : "disabled",
    MCP_API_KEYS_JSON: options.auth ? JSON.stringify([
      { key: apiKey, subject: "http-user@example.com", tenant: "team-http", role: "reader" },
      { key: secondApiKey, subject: "other-user@example.com", tenant: "team-http", role: "reader" },
    ]) : "[]",
    MCP_ALLOWED_ORIGINS: options.origin ?? "",
    MCP_AUDIT_LOG_PATH: "/tmp/not-used-http-audit.jsonl",
  }, { audit: new MemoryAuditSink(), rateLimiter: new IdentityRateLimiter(100, 1_000) });
  context.client = { call: vi.fn(async () => ({ Code: 0, Data: [], RequestConsumed: 0 })) } as unknown as SorftimeCoreClient;
  (context.config.http as { port: number }).port = 0;
  if (options.allowedHosts) (context.config.http as { allowedHosts: string[] }).allowedHosts = options.allowedHosts;
  if (options.maxSessions) (context.config.http as { maxSessions: number }).maxSessions = options.maxSessions;
  const running = startMcpHttpServer(context);
  if (!running.server.listening) await once(running.server, "listening");
  const address = running.server.address() as AddressInfo;
  return { context, running, apiKey, secondApiKey, url: `http://127.0.0.1:${address.port}` };
}

describe("MCP Streamable HTTP lifecycle", () => {
  it("initializes with the official client and returns the same reader tool contract", async () => {
    const { running, url } = await start();
    const client = new Client({ name: "http-contract", version: "1.0.0" });
    const transport = new StreamableHTTPClientTransport(new URL(`${url}/mcp`));
    try {
      await client.connect(transport as unknown as Parameters<Client["connect"]>[0]);
      const { tools } = await client.listTools();
      expect(tools).toHaveLength(4);
      const result = await client.callTool({ name: "sorftime_capabilities", arguments: {} });
      expect(result.structuredContent).toMatchObject({ resultType: "capabilities" });
    } finally {
      await client.close();
      await running.close();
    }
  });

  it("enforces per-user Bearer auth, Origin policy and JSON-RPC batch rejection", async () => {
    const { running, url, apiKey, secondApiKey } = await start({ auth: true, origin: "https://allowed.internal" });
    try {
      const unauthorized = await fetch(`${url}/mcp`, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
      expect(unauthorized.status).toBe(401);
      const wrongOrigin = await fetch(`${url}/mcp`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, origin: "https://evil.example", "content-type": "application/json" },
        body: "{}",
      });
      expect(wrongOrigin.status).toBe(403);
      const batch = await fetch(`${url}/mcp`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, origin: "https://allowed.internal", "content-type": "application/json" },
        body: JSON.stringify([{ jsonrpc: "2.0", id: 1, method: "tools/list" }]),
      });
      expect(batch.status).toBe(400);
      expect(JSON.stringify(await batch.json())).toContain("batch requests are not supported");

      const client = new Client({ name: "authenticated-http", version: "1.0.0" });
      const transport = new StreamableHTTPClientTransport(new URL(`${url}/mcp`), {
        requestInit: { headers: { authorization: `Bearer ${apiKey}`, origin: "https://allowed.internal" } },
      });
      await client.connect(transport as unknown as Parameters<Client["connect"]>[0]);
      expect((await client.listTools()).tools).toHaveLength(4);
      const sessionId = transport.sessionId;
      expect(sessionId).toBeDefined();
      const stolenSession = await fetch(`${url}/mcp`, {
        method: "POST",
        headers: {
          authorization: `Bearer ${secondApiKey}`,
          origin: "https://allowed.internal",
          "mcp-session-id": sessionId!,
          "content-type": "application/json",
        },
        body: JSON.stringify({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} }),
      });
      expect(stolenSession.status).toBe(403);
      await client.close();
      expect(JSON.stringify({ status: unauthorized.status, origin: wrongOrigin.status })).not.toContain(apiKey);
    } finally {
      await running.close();
    }
  });

  it("accepts trusted identity headers only with the separate proxy secret", async () => {
    const proxySecret = "trusted-proxy-secret-which-is-at-least-32-characters";
    const context = await createMcpAppContext({
      NODE_ENV: "test",
      SORFTIME_ACCOUNT_SK: "trusted-header-upstream-sentinel",
      SORFTIME_BASE_URL: "http://127.0.0.1:9999/api/",
      MCP_HTTP_PORT: "3001",
      MCP_AUTH_MODE: "trusted_headers",
      MCP_TRUSTED_PROXY_SECRET: proxySecret,
      MCP_AUDIT_LOG_PATH: "/tmp/not-used-trusted-http-audit.jsonl",
    }, { audit: new MemoryAuditSink(), rateLimiter: new IdentityRateLimiter(100, 1_000) });
    (context.config.http as { port: number }).port = 0;
    const running = startMcpHttpServer(context);
    if (!running.server.listening) await once(running.server, "listening");
    const address = running.server.address() as AddressInfo;
    const url = `http://127.0.0.1:${address.port}/mcp`;
    try {
      const forged = await fetch(url, {
        method: "POST",
        headers: { "content-type": "application/json", "x-company-user": "admin@example.com", "x-company-role": "admin" },
        body: "{}",
      });
      expect(forged.status).toBe(401);
      const gateway = await fetch(url, {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "x-sorftime-proxy-secret": proxySecret,
          "x-company-user": "reader@example.com",
          "x-company-tenant": "team-http",
          "x-company-role": "reader",
        },
        body: "{}",
      });
      expect(gateway.status).toBe(400);
    } finally {
      await running.close();
    }
  });

  it("reports not-ready when the audit sink cannot be written", async () => {
    const { context, running, url } = await start();
    context.audit = {
      record: async () => {},
      checkReady: async () => { throw new Error("audit unavailable"); },
    };
    try {
      const response = await fetch(`${url}/readyz`);
      expect(response.status).toBe(503);
      expect(await response.json()).toEqual({ status: "not_ready", upstreamConfigured: true, auditConfigured: false });
    } finally {
      await running.close();
    }
  });

  it("enforces the configured Host allowlist", async () => {
    const { running, url } = await start({ allowedHosts: ["127.0.0.1"] });
    try {
      expect(await getWithHost(`${url}/healthz`, "evil.example")).toBe(403);
      expect(await getWithHost(`${url}/healthz`, "127.0.0.1")).toBe(200);
    } finally {
      await running.close();
    }
  });

  it("rejects initialization when the session cap is reached", async () => {
    const { running, url } = await start({ maxSessions: 1 });
    const firstClient = new Client({ name: "session-one", version: "1.0.0" });
    const firstTransport = new StreamableHTTPClientTransport(new URL(`${url}/mcp`));
    const secondClient = new Client({ name: "session-two", version: "1.0.0" });
    const secondTransport = new StreamableHTTPClientTransport(new URL(`${url}/mcp`));
    try {
      await firstClient.connect(firstTransport as unknown as Parameters<Client["connect"]>[0]);
      await expect(secondClient.connect(secondTransport as unknown as Parameters<Client["connect"]>[0])).rejects.toThrow();
    } finally {
      await Promise.allSettled([firstClient.close(), secondClient.close()]);
      await running.close();
    }
  });
});
