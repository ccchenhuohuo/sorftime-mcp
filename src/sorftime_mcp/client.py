import asyncio
from dataclasses import dataclass
from typing import Any

import httpx

from sorftime_mcp.config import Settings


@dataclass(frozen=True)
class SorftimeResponse:
    endpoint: str
    domain: int
    estimated_request_cost: int
    request_consumed: int | None
    request_left: int | None
    code: int | None
    message: str | None
    data: Any
    raw_response: dict[str, Any]

    def as_tool_result(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "domain": self.domain,
            "estimatedRequestCost": self.estimated_request_cost,
            "requestConsumed": self.request_consumed,
            "requestLeft": self.request_left,
            "code": self.code,
            "message": self.message,
            "data": self.data,
            "rawResponse": self.raw_response,
        }


class SorftimeClient:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
        self._settings = settings
        self._transport = transport

    async def call(
        self,
        *,
        endpoint: str,
        domain: int,
        payload: dict[str, Any],
        estimated_request_cost: int,
        max_retries: int | None = None,
    ) -> SorftimeResponse:
        response_json = await self._post(endpoint=endpoint, domain=domain, payload=payload, max_retries=max_retries)
        code = _pick(response_json, "code", "Code")
        message = _pick(response_json, "message", "Message")
        return SorftimeResponse(
            endpoint=endpoint,
            domain=domain,
            estimated_request_cost=estimated_request_cost,
            request_consumed=_pick(response_json, "requestConsumed", "RequestConsumed"),
            request_left=_pick(response_json, "requestLeft", "RequestLeft"),
            code=code,
            message=message,
            data=_pick(response_json, "data", "Data"),
            raw_response=response_json,
        )

    async def _post(
        self,
        *,
        endpoint: str,
        domain: int,
        payload: dict[str, Any],
        max_retries: int | None,
    ) -> dict[str, Any]:
        last_error: Exception | None = None
        resolved_max_retries = self._settings.sorftime_api_max_retries if max_retries is None else max_retries
        for attempt in range(resolved_max_retries + 1):
            try:
                return await self._post_once(endpoint=endpoint, domain=domain, payload=payload)
            except httpx.HTTPStatusError as exc:
                last_error = exc
                if not _should_retry_status(exc.response.status_code, attempt, resolved_max_retries):
                    raise
            except (httpx.ConnectError, httpx.NetworkError, httpx.RemoteProtocolError, httpx.TimeoutException) as exc:
                last_error = exc
                if attempt >= resolved_max_retries:
                    raise
            await asyncio.sleep(self._retry_delay(attempt))
        if last_error is not None:
            raise last_error
        raise RuntimeError("Sorftime request failed without an exception")

    async def _post_once(self, *, endpoint: str, domain: int, payload: dict[str, Any]) -> dict[str, Any]:
        headers = {
            "Authorization": f"BasicAuth {self._settings.api_key}",
            "Content-Type": "application/json;charset=UTF-8",
        }
        timeout = httpx.Timeout(self._settings.sorftime_api_timeout_seconds)
        async with httpx.AsyncClient(transport=self._transport, timeout=timeout) as client:
            response = await client.post(
                self.build_url(endpoint=endpoint, domain=domain),
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()
        if not isinstance(data, dict):
            raise ValueError("Sorftime API returned a non-object JSON response")
        return data

    def build_url(self, *, endpoint: str, domain: int) -> str:
        return f"{self._settings.api_base_url}/{endpoint}?domain={domain}"

    def _retry_delay(self, attempt: int) -> float:
        delay = self._settings.sorftime_api_retry_base_delay_seconds * (2**attempt)
        return min(delay, self._settings.sorftime_api_retry_max_delay_seconds)


def _pick(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return None


def _should_retry_status(status_code: int, attempt: int, max_retries: int) -> bool:
    if attempt >= max_retries:
        return False
    return status_code == 429 or status_code >= 500
