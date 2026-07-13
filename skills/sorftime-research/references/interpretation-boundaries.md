# Interpretation boundaries

## Evidence and time

- Keep marketplace, source endpoint, fetched time, monitor time, and warnings attached to every conclusion.
- Distinguish fetch time from the upstream observation time.
- Existing monitoring and subscription data is not automatically realtime.
- Empty data means no matching/available record under the request, not numeric zero.

## Claims

Allowed:

- describe observed rank position, list membership, seller set, stock field, subscription snapshot, or quota state;
- compare two explicitly selected batches when fields are compatible;
- identify mathematical increases/decreases in observed values;
- explain scope, missing data, rate limits, and policy restrictions.

Not allowed:

- infer causality from rank, stock, seller, or list changes;
- claim complete Amazon market coverage from monitored tasks;
- describe shared quota as an employee allowance;
- invent ASIN/TaskId/ScheduleId/NodeId values;
- treat unavailable or missing data as zero;
- conceal that a paid query was unavailable;
- recommend task creation/deletion through MCP.

## Sensitive operational data

- Do not ask for or show the Sorftime Account-SK, MCP API keys, proxy secrets, or Authorization headers.
- Do not include employee identity fields in tool inputs. Identity is transport-derived.
- Account usage and existing async task artifacts may reveal team activity; use them only through admin tools.
- Preserve public `requestId` for support, but never echo server logs or raw error internals.
