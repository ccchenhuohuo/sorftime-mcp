import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { SorftimeCoreClient } from "../src/core/service.js";
import { MemoryAuditSink } from "../src/mcp/audit.js";
import { createMcpAppContext, type McpAppContext } from "../src/mcp/context.js";
import { IdentityRateLimiter } from "../src/mcp/rate-limit.js";
import { createSorftimeMcpServer } from "../src/mcp/server.js";

const closeCallbacks: Array<() => Promise<void>> = [];
afterEach(async () => {
  while (closeCallbacks.length > 0) await closeCallbacks.pop()?.();
});

async function connectedClient(options: {
  role?: "reader" | "admin";
  adminTools?: boolean;
  response?: Record<string, unknown>;
  perIdentityLimit?: number;
} = {}) {
  const audit = new MemoryAuditSink();
  const context = await createMcpAppContext({
    NODE_ENV: "test",
    SORFTIME_ACCOUNT_SK: "mcp-contract-upstream-sentinel",
    SORFTIME_BASE_URL: "http://127.0.0.1:9999/api/",
    MCP_ENABLE_ADMIN_TOOLS: options.adminTools ? "true" : "false",
    MCP_AUDIT_LOG_PATH: "/tmp/not-used-audit.jsonl",
  }, { audit, rateLimiter: new IdentityRateLimiter(options.perIdentityLimit ?? 100, 1_000) });
  const call = vi.fn(async (input: Parameters<SorftimeCoreClient["call"]>[0]) => {
    void input;
    return options.response ?? { Code: 0, Data: [], RequestConsumed: 0, RequestLeft: 500 };
  });
  context.client = { call } as unknown as SorftimeCoreClient;
  const identity = { subject: "alice@example.com", tenant: "team-a", role: options.role ?? "reader", authSource: "api_key" as const };
  const server = createSorftimeMcpServer(context, { identity, transport: "http" });
  const client = new Client({ name: "sorftime-contract-test", version: "1.0.0" });
  const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();
  await server.connect(serverTransport);
  await client.connect(clientTransport);
  closeCallbacks.push(async () => {
    await client.close();
    await server.close();
  });
  return { client, context, call, audit } satisfies { client: Client; context: McpAppContext; call: typeof call; audit: MemoryAuditSink };
}

describe("MCP contract", () => {
  it("publishes only the four ordinary free read-only tools", async () => {
    const { client } = await connectedClient();
    const { tools } = await client.listTools();
    expect(tools.map((tool) => tool.name).sort()).toEqual([
      "sorftime_capabilities",
      "sorftime_check_quota",
      "sorftime_get_monitoring_results",
      "sorftime_list_monitors",
    ]);
    expect(tools.every((tool) => tool.annotations?.readOnlyHint === true)).toBe(true);
    expect(tools.every((tool) => tool.annotations?.destructiveHint === false)).toBe(true);
    expect(tools.every((tool) => {
      if (tool.inputSchema.additionalProperties === false) return true;
      const variants = (tool.inputSchema as { anyOf?: Array<{ additionalProperties?: boolean }> }).anyOf;
      return variants?.every((variant) => variant.additionalProperties === false) === true;
    })).toBe(true);
    expect(tools.map((tool) => tool.name).join(" ")).not.toMatch(/raw|create|delete|update|product|keyword_research/u);
  });

  it("maps a task-oriented monitor call to an exact allowlisted endpoint and audits identity", async () => {
    const { client, call, audit } = await connectedClient();
    const result = await client.callTool({
      name: "sorftime_list_monitors",
      arguments: { marketplace: "US", monitorType: "keyword_ranking", keyword: "power bank", page: 1, pageSize: 20 },
    });
    expect(result.isError).not.toBe(true);
    expect(call).toHaveBeenCalledWith(expect.objectContaining({
      endpoint: "KeywordTasks",
      marketplace: "US",
      body: { Keyword: "power bank", PageIndex: 1, PageSize: 20 },
    }));
    expect(result.structuredContent).toMatchObject({
      schemaVersion: "1.0",
      resultType: "monitor_list:keyword_ranking",
      source: { endpoints: ["KeywordTasks"], billing: "free", requestConsumed: 0 },
    });
    expect(JSON.stringify(result.structuredContent)).not.toContain("RequestLeft");
    expect(audit.events).toHaveLength(2);
    expect(audit.events[0]).toMatchObject({ actor: { subject: "alice@example.com", tenant: "team-a" }, tool: "sorftime_list_monitors", outcome: "started" });
    expect(JSON.stringify(audit.events)).not.toContain("power bank");
    expect(JSON.stringify(audit.events)).not.toContain("mcp-contract-upstream-sentinel");
  });

  it("returns global quota through exactly two free endpoints", async () => {
    const { client, call } = await connectedClient();
    const result = await client.callTool({ name: "sorftime_check_quota", arguments: {} });
    expect(result.isError).not.toBe(true);
    expect(call.mock.calls.map(([input]) => input.endpoint).sort()).toEqual(["CoinQuery", "RequestStreamMonth"]);
    expect(result.structuredContent).toMatchObject({
      resultType: "global_account_quota",
      data: { scope: "global_account", coinRemaining: null, requestRemaining: 500 },
    });
    expect((result.structuredContent as { data: Record<string, unknown> }).data).toEqual({
      scope: "global_account",
      coinRemaining: null,
      requestRemaining: 500,
      note: expect.any(String),
    });
    expect((result.structuredContent as { warnings: string[] }).warnings.join(" ")).toContain("global");
  });

  it("denies admin-only undocumented monitor reads before any upstream call", async () => {
    const { client, call } = await connectedClient();
    const result = await client.callTool({
      name: "sorftime_list_monitors",
      arguments: { marketplace: "US", monitorType: "seller_stock", page: 1, pageSize: 20 },
    });
    expect(result.isError).toBe(true);
    expect(JSON.stringify(result.content)).toContain("FORBIDDEN");
    expect(call).not.toHaveBeenCalled();
  });

  it("rejects unknown or invalid tool inputs before any upstream call", async () => {
    const { client, call } = await connectedClient();
    const unknown = await client.callTool({
      name: "sorftime_list_monitors",
      arguments: { marketplace: "US", monitorType: "best_seller", credential: "must-not-be-accepted" },
    });
    const invalidDate = await client.callTool({
      name: "sorftime_get_monitoring_results",
      arguments: { marketplace: "US", resultType: "best_seller_data", nodeId: "1", listType: 1, at: "2026-02-30 12" },
    });
    const injectedId = await client.callTool({
      name: "sorftime_get_monitoring_results",
      arguments: { marketplace: "US", resultType: "keyword_run_data", scheduleIds: ["schedule-1,schedule-2"] },
    });
    expect(unknown.isError).toBe(true);
    expect(invalidDate.isError).toBe(true);
    expect(injectedId.isError).toBe(true);
    expect(call).not.toHaveBeenCalled();
  });

  it("recursively removes shared account metadata from ordinary tool payloads", async () => {
    const { client } = await connectedClient({
      response: {
        Code: 0,
        Data: [{ id: "monitor-1", RequestLeft: 499, nested: { RequestCount: 2, status: "ready" } }],
        RequestConsumed: 0,
      },
    });
    const result = await client.callTool({
      name: "sorftime_list_monitors",
      arguments: { marketplace: "US", monitorType: "best_seller" },
    });
    const data = (result.structuredContent as { data: { Data: Array<Record<string, unknown>> } }).data;
    expect(data.Data).toEqual([{ id: "monitor-1", nested: { status: "ready" } }]);
  });

  it("conditionally registers two administrator read tools", async () => {
    const { client } = await connectedClient({ role: "admin", adminTools: true });
    const { tools } = await client.listTools();
    expect(tools.map((tool) => tool.name)).toEqual(expect.arrayContaining([
      "sorftime_get_account_usage",
      "sorftime_get_existing_task_result",
    ]));
    expect(tools).toHaveLength(6);
  });

  it("opens a billing circuit if a free endpoint unexpectedly consumes requests", async () => {
    const { client, call, context } = await connectedClient({ response: { Code: 0, Data: [], RequestConsumed: 1 } });
    const first = await client.callTool({ name: "sorftime_list_monitors", arguments: { marketplace: "US", monitorType: "best_seller" } });
    expect((first.structuredContent as { warnings: string[] }).warnings.join(" ")).toContain("blocked");
    const second = await client.callTool({ name: "sorftime_list_monitors", arguments: { marketplace: "US", monitorType: "best_seller" } });
    expect(second.isError).toBe(true);
    expect(JSON.stringify(second.content)).toContain("BILLING_CIRCUIT_OPEN");
    expect(call).toHaveBeenCalledTimes(1);
    expect(context.billingCircuit.blockedReason).toBeDefined();
  });

  it("applies one per-identity rate budget across all tools", async () => {
    const { client, call } = await connectedClient({ perIdentityLimit: 1 });
    const first = await client.callTool({ name: "sorftime_capabilities", arguments: {} });
    const second = await client.callTool({
      name: "sorftime_list_monitors",
      arguments: { marketplace: "US", monitorType: "best_seller" },
    });
    expect(first.isError).not.toBe(true);
    expect(second.isError).toBe(true);
    expect(JSON.stringify(second.content)).toContain("RATE_LIMITED");
    expect(call).not.toHaveBeenCalled();
  });

  it("stops before upstream execution when the audit sink is unavailable", async () => {
    const { client, context, call } = await connectedClient();
    context.audit = {
      record: async () => { throw new Error("audit unavailable"); },
      checkReady: async () => { throw new Error("audit unavailable"); },
    };
    const result = await client.callTool({
      name: "sorftime_list_monitors",
      arguments: { marketplace: "US", monitorType: "best_seller" },
    });
    expect(result.isError).toBe(true);
    expect(call).not.toHaveBeenCalled();
  });
});
