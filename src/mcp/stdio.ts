#!/usr/bin/env node
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { config as loadDotEnv } from "dotenv";
import { createMcpAppContext } from "./context.js";
import { createSorftimeMcpServer } from "./server.js";

loadDotEnv({ quiet: true });

try {
  const context = await createMcpAppContext();
  const server = createSorftimeMcpServer(context, { identity: context.config.stdioIdentity, transport: "stdio" });
  const transport = new StdioServerTransport();
  await server.connect(transport);
  process.stderr.write(`${JSON.stringify({ level: "info", event: "mcp_stdio_started", subject: context.config.stdioIdentity.subject, role: context.config.stdioIdentity.role })}\n`);
  const shutdown = async (): Promise<void> => {
    await server.close();
    process.exit(0);
  };
  process.once("SIGINT", () => void shutdown());
  process.once("SIGTERM", () => void shutdown());
} catch (error) {
  process.stderr.write(`${JSON.stringify({ level: "error", event: "mcp_stdio_start_failed", errorName: error instanceof Error ? error.name : typeof error })}\n`);
  process.exit(1);
}
