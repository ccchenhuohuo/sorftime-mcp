---
name: sorftime-research
description: Use the governed Sorftime MCP to answer questions about shared-account quota, existing keyword/Best Seller/seller-stock monitors, ASIN subscription data, and administrator-approved existing async results. Trigger when users mention Sorftime, Amazon marketplace monitoring, monitored keyword rankings, Best Seller tracking, subscribed ASIN updates, Sorftime quota/points, or ask whether paid Sorftime research is available. Enforce the free read-only policy and never create, update, delete, or silently substitute paid queries.
---

# Sorftime Research

Treat MCP as the execution and policy authority. Use this Skill only for routing, clarification, evidence handling, and bounded interpretation. Never shell out to the CLI for an end-user data request.

## Start with policy discovery

Call `sorftime_capabilities` when the connected server version, enabled admin surface, or policy is uncertain. Trust its response over remembered tool availability. The current compatibility baseline is `free_read_only`; paid reads and every state-changing call are unavailable through MCP.

Do not request or transmit the Sorftime Account-SK. Identity comes from the MCP transport, never from tool arguments.

## Route the request

| User intent | Route |
|---|---|
| Check points, Request balance, or quota status | `sorftime_check_quota` |
| List existing monitors or subscriptions | `sorftime_list_monitors` |
| Read an existing monitor batch/result | `sorftime_get_monitoring_results` |
| Inspect an administrator-owned usage/task result | Use an admin tool only if it appears in `sorftime_capabilities` |
| Realtime product lookup, product search, category analysis, keyword research | Explain that paid reads are not enabled; do not call another tool as a substitute |
| Create/pause/start/delete a monitor or subscription | Explain that mutations are not exposed; direct an administrator to the CLI workflow |

Read [references/mcp-contract.md](references/mcp-contract.md) for exact tool selectors and current reader/admin boundaries. Read [references/workflows.md](references/workflows.md) for multi-step monitor workflows. Read [references/interpretation-boundaries.md](references/interpretation-boundaries.md) before comparing or explaining results.

## Clarify before calling

Ask for the smallest missing selector:

- marketplace for marketplace-specific monitors;
- monitor type when “monitoring” is ambiguous;
- task or schedule ID for execution results;
- NodeId, list type, and exact hour for a Best Seller snapshot;
- one or more 10-character ASINs for subscription data.

Never invent IDs, choose among ambiguous tasks, or turn a product title into an ASIN.

## Execute conservatively

1. Call at most the tool needed for the current step.
2. Do not poll automatically. Ask before fetching multiple batches.
3. Stop on `POLICY_DENIED`, `FORBIDDEN`, `RATE_LIMITED`, or `BILLING_CIRCUIT_OPEN`; preserve the error code and `requestId`.
4. Read `structuredContent`, not only the short text block.
5. Preserve `source.endpoints`, `source.fetchedAt`, `source.requestConsumed`, `warnings`, and `partial` when they affect interpretation.
6. If a supposedly free call reports consumption or opens the billing circuit, stop all further calls and tell the user an administrator must investigate.

## Answer from evidence

- State the marketplace, monitor/result type, and observation time.
- Say “shared account” for quota; never call it the user’s personal balance.
- Distinguish no monitor, no matching record, unavailable data, and a numeric zero.
- Describe observed ranking, seller, stock, or list changes without claiming causes.
- Do not present subscription data as realtime unless the returned timestamp supports that claim.
- If paid research is unavailable, say so directly. Existing monitoring data may be offered only as an explicitly dated alternative, never as a silent replacement.

## Keep execution boundaries intact

- MCP owns authentication, endpoint allowlists, input validation, rate limits, audit logs, billing anomaly detection, and upstream execution.
- The Skill owns intent routing, clarification, source-aware interpretation, and user-facing explanation.
- The CLI remains an administrator/developer tool. Do not invoke its `api call`, login, mutation, or paid commands from this Skill.
