from collections.abc import AsyncIterator
from typing import Any

import pytest

from sorftime_mcp.audit import AuditLogger
from sorftime_mcp.config import Settings


class MemoryAuditLogger(AuditLogger):
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []

    def log(self, record: dict[str, Any]) -> None:
        self.records.append(record)


@pytest.fixture
def settings() -> Settings:
    return Settings(SORFTIME_API_KEY="test-sorftime-key")


class FakeSorftimeClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def call(
        self,
        *,
        endpoint: str,
        domain: int,
        payload: dict[str, Any],
        estimated_request_cost: int,
        max_retries: int | None = None,
    ):
        from sorftime_mcp.client import SorftimeResponse

        self.calls.append(
            {
                "endpoint": endpoint,
                "domain": domain,
                "payload": payload,
                "estimated_request_cost": estimated_request_cost,
                "max_retries": max_retries,
            }
        )
        raw = {
            "Code": 0,
            "Message": None,
            "Data": {"ok": True, "endpoint": endpoint},
            "RequestLeft": 999,
            "requestConsumed": estimated_request_cost,
        }
        return SorftimeResponse(
            endpoint=endpoint,
            domain=domain,
            estimated_request_cost=estimated_request_cost,
            request_consumed=estimated_request_cost,
            request_left=999,
            code=0,
            message=None,
            data=raw["Data"],
            raw_response=raw,
        )


@pytest.fixture
def fake_client() -> FakeSorftimeClient:
    return FakeSorftimeClient()
