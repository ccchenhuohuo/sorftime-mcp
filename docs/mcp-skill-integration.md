# MCP × Skill integration

The MCP service and `sorftime-research` Skill solve different problems and must be installed together for natural-language team use.

- MCP decides who is calling, which endpoint is allowed, whether the call is free/read-only, and records the audit event.
- Skill decides which safe tool matches the user's intent, what selector is missing, and how to describe the returned evidence.

The Skill is not a backup API client. The MCP service is not a natural-language analyst.

## Reader tools

| Tool | Purpose |
|---|---|
| `sorftime_capabilities` | Discover runtime policy, sites and enabled admin surface |
| `sorftime_list_monitors` | List existing keyword/list/subscription monitors |
| `sorftime_get_monitoring_results` | Read exact existing batches/snapshots/subscription data |
| `sorftime_check_quota` | Read shared global Coin and Request status |

Optional admin tools remain free and read-only and require both an admin identity and `MCP_ENABLE_ADMIN_TOOLS=true`.

## Standard workflow

```text
User question
→ Skill identifies quota / monitor list / monitor result / unavailable paid request
→ Skill asks for the smallest missing stable ID
→ MCP validates transport identity and strict input
→ MCP checks the explicit free-read policy and rate limit
→ MCP audits and calls the shared core
→ Skill reads structuredContent and preserves source/warnings/time
→ User receives a bounded answer
```

## Unavailable requests

Realtime product details, product search, category/keyword research, AI task starts, monitor creation/update/delete, and subscriptions are deliberately absent. The Skill must not invoke the CLI or silently use stale monitoring data as a substitute.

An administrator may use the CLI under a separate operational process. That choice and any cost are outside the ordinary MCP session.

## Install the Skill

Codex:

```bash
export CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$CODEX_HOME/skills"
cp -R skills/sorftime-research "$CODEX_HOME/skills/sorftime-research"
```

Claude Code project Skill:

```bash
mkdir -p .claude/skills
cp -R skills/sorftime-research .claude/skills/sorftime-research
```

Restart/reload the Host after installing and connect the Sorftime MCP server. Explicit invocation is `$sorftime-research` in Codex or `/sorftime-research` in Claude Code.

## Contract changes

Tool names, selectors, output fields, error codes, policy boundaries, and interpretation rules are lockstep contracts. Update runtime, Skill references, evals, contract tests and this document together.
