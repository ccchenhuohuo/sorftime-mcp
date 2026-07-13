# Sorftime MCP contract

Treat `sorftime_capabilities` as runtime authority. This reference describes the `1.0.x` free-read-only baseline and is not a second endpoint registry.

## Reader tools

### `sorftime_capabilities`

Use with `{}` to discover policy version, marketplaces, enabled admin surface, and disabled capability classes. It does not call Sorftime.

### `sorftime_check_quota`

Use with `{}`. It reads global Coin and Request status through free endpoints. The result is shared-account state, never a personal employee quota. Preserve the global-scope warning.

### `sorftime_list_monitors`

Required:

- `marketplace`: `US|GB|DE|FR|IN|CA|JP|ES|IT|MX|AE|AU|BR|SA`;
- `monitorType`: `keyword_ranking|best_seller|asin_subscription|seller_stock`.

Optional keyword-monitor filters are `keyword` and `taskIds`; do not use them for other monitor types. Pagination uses `page` and `pageSize` (`20..200`). `seller_stock` list access is administrator-only because the upstream request schema is undocumented.

### `sorftime_get_monitoring_results`

Use one `resultType`:

| `resultType` | Required selectors | Meaning |
|---|---|---|
| `keyword_runs` | `marketplace`, `taskId`; optional `date` | List execution batches for one keyword task |
| `keyword_run_data` | `marketplace`, `scheduleIds` (1–20) | Read exact keyword batch details |
| `best_seller_data` | `marketplace`, `nodeId`, `listType` (`1|3|4|5`), `at` (`YYYY-MM-DD HH`) | Read one monitored list snapshot |
| `seller_runs` | `marketplace`, `taskId` | List seller/stock execution batches |
| `seller_run_data` | `marketplace`, `scheduleId` | Read one seller/stock batch |
| `asin_subscription_data` | `marketplace`, `asins` (1–100 valid ASINs) | Read current data for active subscriptions |

Do not guess TaskId, ScheduleId, NodeId, list type, hour, or ASIN.

## Administrator tools

They appear only when server configuration enables them and the authenticated identity is an admin:

- `sorftime_get_account_usage`: detailed shared Coin usage by marketplace/date;
- `sorftime_get_existing_task_result`: existing review status, image-search status/result, or AI result by known identifier.

Admin tools remain read-only. They do not make paid calls or create tasks.

## Unified result

Read `schemaVersion`, `requestId`, `marketplace`, `resultType`, `data`, `source`, `warnings`, and `partial`. Preserve `source.endpoints`, `source.fetchedAt`, `source.billing`, and `source.requestConsumed` when explaining evidence.

Ordinary monitoring tools remove shared-account quota metadata. Only quota/account-usage tools retain it.

## Error handling

- `POLICY_DENIED`: requested capability is outside free read-only policy;
- `FORBIDDEN`: authenticated role lacks access;
- `RATE_LIMITED`: stop and honor `retryAfterSeconds`; do not immediately retry;
- `BILLING_CIRCUIT_OPEN`: a free endpoint reported consumption; stop all calls and escalate;
- `UPSTREAM_ERROR`: report `requestId`; do not expose or infer upstream internals.
