import { createHash } from "node:crypto";
import { mkdir, open } from "node:fs/promises";
import { dirname } from "node:path";
import { ValidationError } from "../errors.js";
import type { McpIdentity } from "./config.js";

export type AuditDecision = "allow" | "deny";
export type AuditOutcome = "started" | "success" | "error" | "rate_limited" | "policy_denied";

export interface AuditEvent {
  timestamp: string;
  requestId: string;
  event: "tool_start" | "tool_finish" | "tool_denied";
  actor: Pick<McpIdentity, "subject" | "tenant" | "role" | "authSource">;
  transport: "stdio" | "http";
  tool: string;
  marketplace: string | null;
  endpoints: string[];
  inputFingerprint: string;
  inputKeys: string[];
  decision: AuditDecision;
  outcome: AuditOutcome;
  durationMs?: number;
  errorCode?: string;
  requestConsumed?: number;
}

function stableValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(stableValue);
  if (!value || typeof value !== "object") return value;
  return Object.fromEntries(
    Object.entries(value as Record<string, unknown>)
      .sort(([left], [right]) => left.localeCompare(right))
      .map(([key, item]) => [key, stableValue(item)]),
  );
}

export function fingerprintInput(value: unknown): string {
  return createHash("sha256").update(JSON.stringify(stableValue(value))).digest("hex");
}

export interface AuditSink {
  record(event: AuditEvent): Promise<void>;
  checkReady(): Promise<void>;
}

export class FileAuditSink implements AuditSink {
  private queue: Promise<void> = Promise.resolve();

  constructor(private readonly path: string) {}

  async checkReady(): Promise<void> {
    try {
      await mkdir(dirname(this.path), { recursive: true, mode: 0o700 });
      const handle = await open(this.path, "a", 0o600);
      try {
        await handle.chmod(0o600);
      } finally {
        await handle.close();
      }
    } catch {
      throw new ValidationError("Audit log is unavailable; governed tool execution was stopped.");
    }
  }

  record(event: AuditEvent): Promise<void> {
    const write = async (): Promise<void> => {
      try {
        await mkdir(dirname(this.path), { recursive: true, mode: 0o700 });
        const handle = await open(this.path, "a", 0o600);
        try {
          await handle.appendFile(`${JSON.stringify(event)}\n`, "utf8");
          await handle.chmod(0o600);
        } finally {
          await handle.close();
        }
      } catch {
        throw new ValidationError("Audit log is unavailable; governed tool execution was stopped.");
      }
    };
    this.queue = this.queue.then(write, write);
    return this.queue;
  }
}

export class MemoryAuditSink implements AuditSink {
  readonly events: AuditEvent[] = [];

  async checkReady(): Promise<void> {}

  async record(event: AuditEvent): Promise<void> {
    this.events.push(structuredClone(event));
  }
}
