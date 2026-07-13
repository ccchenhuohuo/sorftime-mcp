import { timingSafeEqual } from "node:crypto";
import type { Request } from "express";
import type { McpIdentity, McpRuntimeConfig } from "./config.js";

function secureEquals(left: string, right: string): boolean {
  const leftBytes = Buffer.from(left);
  const rightBytes = Buffer.from(right);
  return leftBytes.length === rightBytes.length && timingSafeEqual(leftBytes, rightBytes);
}

function cleanIdentityHeader(value: string | undefined): string | undefined {
  const cleaned = value?.trim();
  return cleaned && /^[A-Za-z0-9@._:+-]{1,200}$/u.test(cleaned) ? cleaned : undefined;
}

export function authenticateHttpRequest(config: McpRuntimeConfig, request: Request): McpIdentity | undefined {
  if (config.http.authMode === "disabled") {
    return { subject: "anonymous-local", tenant: "local", role: "reader", authSource: "disabled" };
  }
  if (config.http.authMode === "api_key") {
    const header = request.header("authorization");
    const token = header?.startsWith("Bearer ") ? header.slice("Bearer ".length) : undefined;
    if (!token) return undefined;
    const record = config.http.apiKeyIdentities.find((candidate) => secureEquals(token, candidate.key));
    if (!record) return undefined;
    return { subject: record.subject, tenant: record.tenant, role: record.role, authSource: "api_key" };
  }

  const proxySecret = request.header("x-sorftime-proxy-secret");
  if (!proxySecret || !config.http.trustedProxySecret || !secureEquals(proxySecret, config.http.trustedProxySecret)) return undefined;
  const subject = cleanIdentityHeader(request.header("x-company-user"));
  const tenant = cleanIdentityHeader(request.header("x-company-tenant")) ?? "default";
  const roleHeader = request.header("x-company-role");
  if (!subject || (roleHeader !== undefined && !["reader", "admin"].includes(roleHeader))) return undefined;
  return {
    subject,
    tenant,
    role: roleHeader === "admin" ? "admin" : "reader",
    authSource: "trusted_headers",
  };
}

export function sameIdentity(left: McpIdentity, right: McpIdentity): boolean {
  return left.subject === right.subject && left.tenant === right.tenant && left.role === right.role;
}
