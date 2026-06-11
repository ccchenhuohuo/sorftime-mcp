import httpx

from sorftime_mcp.client import SorftimeClient


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
