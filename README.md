# Sorftime MCP Server

Remote MCP server for read-only Sorftime Enterprise API access. It keeps the Sorftime Account-SK on the server, authenticates colleagues with per-user Bearer JWTs, and writes JSON audit logs for every call.

## Public Tools

The server exposes 10 MCP tools. High-frequency methods have shortcut tools; all other safe read-only methods are available through the strict registry-backed `sorftime_call` router.

| Tool | Purpose |
| --- | --- |
| `sorftime_methods` | List supported Sorftime methods, categories, costs, async flags, and shortcuts. |
| `sorftime_method_schema` | Get schema, required/optional params, examples, and cost notes for one method. |
| `sorftime_call` | Call any whitelisted read-only method with validated Sorftime-native params. |
| `product_request` | Shortcut for `ProductRequest`. |
| `category_request` | Shortcut for `CategoryRequest`. |
| `keyword_request` | Shortcut for `KeywordRequest`. |
| `product_query` | Shortcut for `ProductQuery`. |
| `category_trend` | Shortcut for `CategoryTrend`. |
| `request_stream_month` | Shortcut for `RequestStreamMonth`. |
| `coin_query` | Shortcut for `CoinQuery`. |

Mutating account tools and subscription/monitoring management endpoints are intentionally excluded from v1.

Every API call returns:

```json
{
  "endpoint": "ProductRequest",
  "domain": 1,
  "estimatedRequestCost": 1,
  "requestConsumed": 1,
  "requestLeft": 1200,
  "data": {},
  "rawResponse": {}
}
```

`domain` defaults to `1` (`US`). Discovery responses include the full Sorftime domain mapping:

| domain | Site |
| --- | --- |
| 1 | US 美国 |
| 2 | GB 英国 |
| 3 | DE 德国 |
| 4 | FR 法国 |
| 5 | IN 印度 |
| 6 | CA 加拿大 |
| 7 | JP 日本 |
| 8 | ES 西班牙 |
| 9 | IT 意大利 |
| 10 | MX 墨西哥 |
| 11 | AE 阿联酋 |
| 12 | AU 澳大利亚 |
| 13 | BR 巴西 |
| 14 | SA 沙特阿拉伯 |

Historical backfill is not supported for IN, AE, AU, BR, or SA.

## Router Examples

List supported methods:

```json
{
  "input": {
    "category": "product"
  }
}
```

Get a method schema:

```json
{
  "input": {
    "method": "ProductRequest"
  }
}
```

Call a low-frequency method through `sorftime_call`:

```json
{
  "input": {
    "method": "ASINKeywordRanking",
    "domain": 1,
    "params": {
      "Keyword": "power bank",
      "ASIN": "B07CZDXDG8",
      "QueryStart": "2024-12-01",
      "QueryEnd": "2025-01-01",
      "Page": 1
    }
  }
}
```

Shortcut tools use friendlier snake_case params:

```json
{
  "input": {
    "asin": "B0CVM8TXHP",
    "trend": 1
  }
}
```

Internally, shortcuts and `sorftime_call` use the same registry, validator, cost estimator, Sorftime client, and audit logger.

## Local Setup

```bash
cd mcp/sorftime-mcp
cp .env.example .env
uv sync
```

Set these values in `.env` or in your deployment secret store:

```bash
SORFTIME_API_KEY=...
SORFTIME_MCP_JWT_SECRET=...
SORFTIME_MCP_ISSUER=sorftime-mcp
SORFTIME_MCP_AUDIENCE=sorftime-mcp-users
```

Do not commit the real Sorftime Account-SK.

Optional tuning:

```bash
SORFTIME_API_TIMEOUT_SECONDS=120
SORFTIME_API_MAX_RETRIES=3
SORFTIME_API_RETRY_BASE_DELAY_SECONDS=2
SORFTIME_API_RETRY_MAX_DELAY_SECONDS=15
SORFTIME_AUDIT_LOG_PATH=logs/sorftime-mcp-audit.jsonl
```

## Issue Colleague Tokens

```bash
uv run sorftime-mcp issue-token --user alice --expires-days 30
```

The token is a Bearer JWT. Audit logs use the JWT `sub` claim as the caller identity.

## Run Locally

Stdio mode for local MCP clients such as Codex:

```bash
uv run sorftime-mcp stdio
```

In stdio mode, audit logs are not emitted to stdout because stdout is reserved for the MCP protocol. Set `SORFTIME_AUDIT_LOG_PATH` if you want local audit logs.

HTTP mode for remote deployment:

```bash
uv run sorftime-mcp serve --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

MCP endpoint:

```text
http://localhost:8000/mcp
```

Clients must send:

```http
Authorization: Bearer <issued-token>
```

## Codex MCP Config

Example stdio configuration:

```toml
[mcp_servers.sorftime]
command = "uvx"
args = ["--from", "git+https://github.com/ccchenhuohuo/sorftime-mcp.git", "sorftime-mcp", "stdio"]
startup_timeout_sec = 180

[mcp_servers.sorftime.env]
SORFTIME_API_KEY = "replace-with-server-side-account-sk"
SORFTIME_MCP_JWT_SECRET = "replace-with-long-random-string"
SORFTIME_AUDIT_LOG_PATH = "/Users/chenyu/.codex/logs/sorftime_mcp_audit.jsonl"
```

## OpenCloud Deployment

Build and deploy this directory as a container. Configure secrets in OpenCloud environment variables, not in the image:

```bash
docker build -t sorftime-mcp .
docker run -p 8000:8000 \
  -e SORFTIME_API_KEY=... \
  -e SORFTIME_MCP_JWT_SECRET=... \
  -e SORFTIME_MCP_ISSUER=sorftime-mcp \
  -e SORFTIME_MCP_AUDIENCE=sorftime-mcp-users \
  sorftime-mcp
```

The Docker command starts:

```bash
uvicorn sorftime_mcp.server:create_app --factory --host 0.0.0.0 --port 8000
```

## Audit Logs

Audit records are JSON lines written to stdout. Set `SORFTIME_AUDIT_LOG_PATH=logs/sorftime-mcp-audit.jsonl` to also write locally.

Each record includes timestamp, user, endpoint, domain, sanitized parameter summary, estimated request cost, actual consumed value when Sorftime returns it, requestLeft, latency, status, and Sorftime code/message.

Secrets, bearer tokens, authorization headers, and base64 images are redacted.

## Tests

```bash
uv run pytest
```
