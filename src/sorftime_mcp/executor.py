import time
from typing import Any

from fastmcp.server.dependencies import get_access_token
from pydantic import BaseModel

from sorftime_mcp.audit import AuditLogger, sanitize_for_audit, utc_now_iso
from sorftime_mcp.catalog import MethodDefinition, get_method_definition, make_model_input
from sorftime_mcp.client import SorftimeClient, SorftimeResponse
from sorftime_mcp.models import SorftimeCallInput, SorftimeInput


class ToolExecutor:
    def __init__(self, *, client: SorftimeClient, audit_logger: AuditLogger) -> None:
        self._client = client
        self._audit_logger = audit_logger

    async def execute_shortcut(self, method: str, input_model: BaseModel | dict[str, Any]) -> dict[str, Any]:
        definition = get_method_definition(method)
        model = definition.input_model.model_validate(input_model)
        if not isinstance(model, SorftimeInput):
            raise TypeError("Sorftime tool input model must inherit from SorftimeInput")
        return await self.execute_method(definition, model)

    async def execute_sorftime_call(self, input_model: BaseModel | dict[str, Any]) -> dict[str, Any]:
        call = SorftimeCallInput.model_validate(input_model)
        definition = get_method_definition(call.method)
        model = make_model_input(definition, domain=call.domain, params=call.params)
        return await self.execute_method(definition, model)

    async def execute_method(self, definition: MethodDefinition, model: SorftimeInput) -> dict[str, Any]:
        payload = model.to_payload()
        estimated_cost = definition.estimate_cost(model)
        user = current_user()
        start = time.perf_counter()
        response: SorftimeResponse | None = None
        status = "ok"
        error_message: str | None = None
        try:
            response = await self._client.call(
                endpoint=definition.endpoint,
                domain=model.domain,
                payload=payload,
                estimated_request_cost=estimated_cost,
            )
            if response.code not in (None, 0):
                status = "sorftime_error"
            return response.as_tool_result()
        except Exception as exc:
            status = "error"
            error_message = str(exc)
            raise
        finally:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            self._audit_logger.log(
                {
                    "timestamp": utc_now_iso(),
                    "user": user,
                    "endpoint": definition.endpoint,
                    "domain": model.domain,
                    "params": sanitize_for_audit(payload),
                    "estimatedRequestCost": estimated_cost,
                    "requestConsumed": response.request_consumed if response is not None else None,
                    "requestLeft": response.request_left if response is not None else None,
                    "latencyMs": latency_ms,
                    "status": status,
                    "sorftimeCode": response.code if response is not None else None,
                    "sorftimeMessage": response.message if response is not None else error_message,
                }
            )


def current_user() -> str:
    try:
        token = get_access_token()
    except RuntimeError:
        return "anonymous"
    if token is None:
        return "anonymous"
    claims = getattr(token, "claims", None)
    if isinstance(claims, dict) and isinstance(claims.get("sub"), str):
        return claims["sub"]
    client_id = getattr(token, "client_id", None)
    if isinstance(client_id, str) and client_id != "":
        return client_id
    return "anonymous"
