#!/usr/bin/env node
import { config as loadDotEnv } from "dotenv";
import { createMcpAppContext } from "./context.js";
import { startMcpHttpServer } from "./http-server.js";

loadDotEnv({ quiet: true });

try {
  const context = await createMcpAppContext();
  const running = startMcpHttpServer(context);
  let stopping = false;
  const shutdown = async (): Promise<void> => {
    if (stopping) return;
    stopping = true;
    await running.close();
    process.exit(0);
  };
  process.once("SIGINT", () => void shutdown());
  process.once("SIGTERM", () => void shutdown());
} catch (error) {
  process.stderr.write(`${JSON.stringify({ level: "error", event: "mcp_http_start_failed", errorName: error instanceof Error ? error.name : typeof error })}\n`);
  process.exit(1);
}
