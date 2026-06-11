import jwt
import httpx
from datetime import datetime, timedelta, timezone

from sorftime_mcp.auth import create_auth_provider, issue_token
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


def test_issue_token_contains_expected_claims(settings) -> None:
    token = issue_token(settings=settings, user="alice", expires_days=1)
    decoded = jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        issuer=settings.sorftime_mcp_issuer,
        audience=settings.sorftime_mcp_audience,
    )

    assert decoded["sub"] == "alice"


async def test_auth_provider_accepts_valid_token(settings) -> None:
    provider = create_auth_provider(settings)
    token = issue_token(settings=settings, user="alice", expires_days=1)

    access_token = await provider.verify_token(token)

    assert access_token is not None
    assert access_token.client_id == "alice"
    assert access_token.claims["sub"] == "alice"


async def test_auth_provider_rejects_missing_invalid_and_expired_tokens(settings) -> None:
    provider = create_auth_provider(settings)
    expired_token = jwt.encode(
        {
            "sub": "alice",
            "iss": settings.sorftime_mcp_issuer,
            "aud": settings.sorftime_mcp_audience,
            "iat": datetime.now(timezone.utc) - timedelta(days=2),
            "nbf": datetime.now(timezone.utc) - timedelta(days=2),
            "exp": datetime.now(timezone.utc) - timedelta(days=1),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )

    assert await provider.verify_token("") is None
    assert await provider.verify_token("not-a-token") is None
    assert await provider.verify_token(expired_token) is None
