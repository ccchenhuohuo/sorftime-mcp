from typing import Any

from fastmcp import FastMCP
from starlette.responses import JSONResponse

from sorftime_mcp.audit import AuditLogger
from sorftime_mcp.auth import create_auth_provider
from sorftime_mcp.catalog import (
    METHOD_DEFINITIONS,
    PUBLIC_TOOL_DEFINITIONS,
    PublicToolDefinition,
    get_method_definition,
    method_schema,
    method_summary,
)
from sorftime_mcp.client import SorftimeClient
from sorftime_mcp.config import Settings, load_settings
from sorftime_mcp.domains import domains_payload
from sorftime_mcp.executor import ToolExecutor
from sorftime_mcp.models import SorftimeMethodSchemaInput, SorftimeMethodsInput


def create_mcp(
    *,
    settings: Settings | None = None,
    client: SorftimeClient | None = None,
    audit_logger: AuditLogger | None = None,
    enable_auth: bool = True,
) -> FastMCP:
    resolved_settings = settings or load_settings()
    auth_provider = create_auth_provider(resolved_settings) if enable_auth else None
    mcp = FastMCP(name="Sorftime API MCP", auth=auth_provider)

    @mcp.custom_route("/health", methods=["GET"], include_in_schema=False)
    async def health(_: Any) -> JSONResponse:
        return JSONResponse({"status": "ok", "service": "sorftime-mcp"})

    executor = ToolExecutor(
        client=client or SorftimeClient(resolved_settings),
        audit_logger=audit_logger or AuditLogger(resolved_settings.sorftime_audit_log_path),
    )
    for definition in PUBLIC_TOOL_DEFINITIONS:
        register_tool(mcp, executor, definition)
    return mcp


def create_app(settings: Settings | None = None):
    mcp = create_mcp(settings=settings)
    return mcp.http_app(path="/mcp")


def register_tool(mcp: FastMCP, executor: ToolExecutor, definition: PublicToolDefinition) -> None:
    async def generated_tool(input: Any) -> dict[str, Any]:
        if definition.kind == "methods":
            model = SorftimeMethodsInput.model_validate(input)
            methods = [
                method_summary(method_definition)
                for method_definition in METHOD_DEFINITIONS
                if model.category is None or method_definition.category == model.category
            ]
            return {"count": len(methods), "domains": domains_payload(), "methods": methods}
        if definition.kind == "schema":
            model = SorftimeMethodSchemaInput.model_validate(input)
            return method_schema(get_method_definition(model.method))
        if definition.kind == "call":
            return await executor.execute_sorftime_call(input)
        if definition.method is None:
            raise ValueError(f"Public tool {definition.name} has no method binding")
        return await executor.execute_shortcut(definition.method, input)

    generated_tool.__name__ = definition.name
    generated_tool.__qualname__ = definition.name
    generated_tool.__doc__ = definition.description
    generated_tool.__annotations__ = {"input": definition.input_model, "return": dict[str, Any]}
    mcp.tool(name=definition.name)(generated_tool)
