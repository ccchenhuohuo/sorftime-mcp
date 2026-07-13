# Deployment and production checklist

## Recommended topology

```text
Employee → Company OAuth/OIDC gateway → Sorftime MCP HTTP → Sorftime API
                                      ↘ audit sink / monitoring
```

The gateway authenticates employees and sends trusted identity headers over a private connection. MCP validates a separate `MCP_TRUSTED_PROXY_SECRET`; direct clients cannot self-assert identity or role.

Per-user API keys are supported for an initial controlled rollout, but are not equivalent to company SSO.

## Secrets

- Put the Sorftime Account-SK only in a Secret Manager or mounted file (`SORFTIME_ACCOUNT_SK_FILE`).
- Store `MCP_API_KEYS_JSON` or `MCP_TRUSTED_PROXY_SECRET` in the deployment secret system.
- Keep gateway and Sorftime credentials distinct.
- Never bake secrets into images, environment examples, MCP client configs, Skill files, or repository history.

## HTTP requirements

- Set `NODE_ENV=production`.
- Use `MCP_AUTH_MODE=api_key` or `trusted_headers`; disabled mode fails closed.
- Terminate TLS at an approved gateway/load balancer.
- Bind to a private interface and configure `MCP_ALLOWED_HOSTS`.
- Configure browser Origins only when needed.
- Set session, concurrency, per-user and global rate limits.
- Persist and protect `MCP_AUDIT_LOG_PATH`; define retention and access policy.

## Identity gateway headers

In `trusted_headers` mode the trusted gateway sends:

- `X-Sorftime-Proxy-Secret`;
- `X-Company-User`;
- `X-Company-Tenant`;
- optional `X-Company-Role: reader|admin`.

Strip any client-provided copies before injecting these headers. Do not expose the MCP service directly to users in this mode.

## Container

```bash
docker build -t sorftime-mcp:1.0.0 .
docker run --rm -p 3000:3000 \
  --env-file /secure/path/sorftime-mcp.env \
  -v /secure/audit:/app/var \
  sorftime-mcp:1.0.0
```

Health endpoints:

- `/healthz`: process health and policy version;
- `/readyz`: validated startup configuration. It intentionally does not spend quota on every probe.

## Before team rollout

- [ ] Company gateway/OIDC integration tested with real reader/admin identities.
- [ ] Sorftime Account-SK mounted from Secret Manager.
- [ ] Private DNS, TLS and Host allowlist configured.
- [ ] Audit retention, rotation, backup and reviewer access defined.
- [ ] Alert on `BILLING_CIRCUIT_OPEN`, Sorftime 501/429, upstream timeouts and auth failures.
- [ ] Rate/concurrency values load-tested against one Account-SK.
- [ ] Multi-replica session/rate/audit strategy defined, or deployment fixed to one replica.
- [ ] Skill installed in approved Hosts and policy-denial evals reviewed.
- [ ] `pnpm check`, Skill validator, secret scan and container smoke pass.
- [ ] Only free read-only live verification executed before launch.
