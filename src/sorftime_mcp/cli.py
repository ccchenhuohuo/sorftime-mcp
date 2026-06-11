import click
import uvicorn

from sorftime_mcp.audit import AuditLogger
from sorftime_mcp.auth import issue_token
from sorftime_mcp.config import load_settings
from sorftime_mcp.server import create_mcp


@click.group()
def cli() -> None:
    """Sorftime MCP server administration."""


@cli.command("issue-token")
@click.option("--user", required=True, help="Colleague identifier for the JWT sub claim.")
@click.option("--expires-days", default=30, show_default=True, type=click.IntRange(min=1))
def issue_token_command(user: str, expires_days: int) -> None:
    """Issue a per-user Bearer JWT for MCP access."""
    try:
        settings = load_settings()
        token = issue_token(settings=settings, user=user, expires_days=expires_days)
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    click.echo(token)


@cli.command("serve")
@click.option("--host", default="0.0.0.0", show_default=True)
@click.option("--port", default=8000, show_default=True, type=int)
def serve_command(host: str, port: int) -> None:
    """Run the HTTP MCP server."""
    uvicorn.run(
        "sorftime_mcp.server:create_app",
        factory=True,
        host=host,
        port=port,
    )


@cli.command("stdio")
def stdio_command() -> None:
    """Run the MCP server over stdio for local MCP clients."""
    try:
        settings = load_settings()
        mcp = create_mcp(
            settings=settings,
            audit_logger=AuditLogger(settings.sorftime_audit_log_path, emit_stdout=False),
            enable_auth=False,
        )
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    mcp.run(transport="stdio", show_banner=False)
