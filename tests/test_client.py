import httpx
import pytest
from pydantic import ValidationError

from sorftime_mcp.client import SorftimeClient
from sorftime_mcp.config import SORFTIME_API_BASE_URL, Settings


def test_settings_do_not_load_local_env_or_override_base_url(tmp_path, monkeypatch) -> None:
    (tmp_path / ".env").write_text(
        "SORFTIME_API_KEY=env-file-key\nSORFTIME_API_BASE_URL=https://example.invalid/api\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SORFTIME_API_KEY", raising=False)
    monkeypatch.delenv("SORFTIME_API_BASE_URL", raising=False)

    with pytest.raises(ValidationError):
        Settings()

    settings = Settings(SORFTIME_API_KEY="explicit-key")

    assert settings.api_key == "explicit-key"
    assert settings.api_base_url == SORFTIME_API_BASE_URL


async def test_client_builds_url_headers_and_normalizes_response(settings) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://standardapi.sorftime.com/api/ProductRequest?domain=1"
        assert request.headers["Authorization"] == "BasicAuth test-sorftime-key"
        assert request.headers["Content-Type"] == "application/json;charset=UTF-8"
        assert request.content == b'{"ASIN":"B000000001"}'
        return httpx.Response(
            200,
            json={
                "Code": 0,
                "Message": None,
                "Data": {"Title": "Sample"},
                "RequestLeft": 100,
                "requestConsumed": 1,
            },
        )

    client = SorftimeClient(settings, transport=httpx.MockTransport(handler))

    result = await client.call(
        endpoint="ProductRequest",
        domain=1,
        payload={"ASIN": "B000000001"},
        estimated_request_cost=1,
    )

    assert result.as_tool_result()["data"] == {"Title": "Sample"}
    assert result.request_left == 100
    assert result.request_consumed == 1


async def test_client_retries_retryable_status(settings) -> None:
    settings.sorftime_api_retry_base_delay_seconds = 0.001
    calls = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(500, json={"Code": 500, "Message": "temporary"})
        return httpx.Response(200, json={"Code": 0, "Data": {"ok": True}})

    client = SorftimeClient(settings, transport=httpx.MockTransport(handler))

    result = await client.call(
        endpoint="ProductRequest",
        domain=1,
        payload={"ASIN": "B000000001"},
        estimated_request_cost=1,
    )

    assert calls == 2
    assert result.data == {"ok": True}


async def test_client_can_disable_retries_for_non_idempotent_methods(settings) -> None:
    calls = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500, json={"Code": 500, "Message": "temporary"})

    client = SorftimeClient(settings, transport=httpx.MockTransport(handler))

    with pytest.raises(httpx.HTTPStatusError):
        await client.call(
            endpoint="ProductAssistant",
            domain=1,
            payload={"Asin": "B000000001", "Type": 0},
            estimated_request_cost=25,
            max_retries=0,
        )

    assert calls == 1
