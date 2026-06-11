import click

from sorftime_mcp.audit import AuditLogger
from sorftime_mcp.config import load_settings
from sorftime_mcp.server import create_mcp


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """Run the Sorftime MCP server over stdio."""
    if ctx.invoked_subcommand is None:
        run_stdio()


@cli.command("stdio")
def stdio_command() -> None:
    """Run the MCP server over stdio."""
    run_stdio()


def run_stdio() -> None:
    try:
        settings = load_settings()
        mcp = create_mcp(
            settings=settings,
            audit_logger=AuditLogger(settings.sorftime_audit_log_path, emit_stdout=False),
        )
    except Exception as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
    mcp.run(transport="stdio", show_banner=False)
