import { randomUUID } from "node:crypto";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { CliError } from "../errors.js";

export class McpPublicError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly retryable = false,
    readonly details: Record<string, unknown> = {},
    readonly requestId?: string,
  ) {
    super(message);
    this.name = "McpPublicError";
  }
}

export function toolSuccess(data: object, summary: string): CallToolResult {
  return {
    content: [{ type: "text", text: summary }],
    structuredContent: data as Record<string, unknown>,
  };
}

export function toolError(error: unknown, fallbackRequestId = randomUUID()): CallToolResult {
  const requestId = error instanceof McpPublicError && error.requestId ? error.requestId : fallbackRequestId;
  const publicError = error instanceof McpPublicError
    ? {
        code: error.code,
        message: error.message,
        details: error.details,
        retryable: error.retryable,
        requestId,
      }
    : error instanceof CliError
      ? {
          code: "UPSTREAM_ERROR",
          message: "Sorftime upstream request failed. Contact the service owner with requestId.",
          details: {},
          retryable: error.exitCode === 4,
          requestId,
        }
      : {
          code: "INTERNAL_ERROR",
          message: "The MCP service failed unexpectedly. Contact the service owner with requestId.",
          details: {},
          retryable: false,
          requestId,
        };

  process.stderr.write(`${JSON.stringify({
    level: "error",
    event: "mcp_tool_error",
    requestId,
    code: publicError.code,
    errorName: error instanceof Error ? error.name : typeof error,
  })}\n`);
  return {
    content: [{ type: "text", text: JSON.stringify({ error: publicError }) }],
    structuredContent: { error: publicError },
    isError: true,
  };
}
