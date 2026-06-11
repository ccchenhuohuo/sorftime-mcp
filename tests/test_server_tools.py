import pytest
from fastmcp import Client

from sorftime_mcp.catalog import (
    HIGH_FREQUENCY_METHODS,
    METHOD_DEFINITIONS,
    METHOD_REGISTRY,
    PUBLIC_TOOL_NAMES,
    UNSAFE_METHODS,
)
from sorftime_mcp.server import create_mcp


async def test_mcp_lists_exactly_public_tools(settings, fake_client) -> None:
    mcp = create_mcp(settings=settings, client=fake_client, enable_auth=False)

    async with Client(mcp) as client:
        tools = await client.list_tools()

    assert {tool.name for tool in tools} == set(PUBLIC_TOOL_NAMES)
    assert len(tools) == 10


async def test_discovery_tools_return_method_summary_and_schema(settings, fake_client) -> None:
    mcp = create_mcp(settings=settings, client=fake_client, enable_auth=False)

    async with Client(mcp) as client:
        methods_result = await client.call_tool("sorftime_methods", {"input": {"category": "product"}})
        schema_result = await client.call_tool("sorftime_method_schema", {"input": {"method": "ProductRequest"}})

    assert methods_result.data["count"] > 0
    assert all(method["category"] == "product" for method in methods_result.data["methods"])
    assert schema_result.data["method"] == "ProductRequest"
    assert schema_result.data["required"] == ["ASIN"]
    assert schema_result.data["shortcutTool"] == "product_request"
    assert schema_result.data["examples"]
    assert "jsonSchema" in schema_result.data


async def test_sorftime_call_routes_low_frequency_method(settings, fake_client) -> None:
    mcp = create_mcp(settings=settings, client=fake_client, enable_auth=False)

    async with Client(mcp) as client:
        result = await client.call_tool(
            "sorftime_call",
            {
                "input": {
                    "method": "ASINKeywordRanking",
                    "domain": 1,
                    "params": {
                        "Keyword": "power bank",
                        "ASIN": "B07CZDXDG8",
                        "QueryStart": "2024-12-01",
                        "QueryEnd": "2025-01-01",
                        "Page": 1,
                    },
                }
            },
        )

    assert fake_client.calls == [
        {
            "endpoint": "ASINKeywordRanking",
            "domain": 1,
            "payload": {
                "Keyword": "power bank",
                "ASIN": "B07CZDXDG8",
                "QueryStart": "2024-12-01",
                "QueryEnd": "2025-01-01",
                "Page": 1,
            },
            "estimated_request_cost": 2,
        }
    ]
    assert result.data["endpoint"] == "ASINKeywordRanking"


async def test_sorftime_call_rejects_unknown_method_and_invalid_params(settings, fake_client) -> None:
    mcp = create_mcp(settings=settings, client=fake_client, enable_auth=False)

    async with Client(mcp) as client:
        with pytest.raises(Exception):
            await client.call_tool("sorftime_call", {"input": {"method": "FavoriteKeyword", "params": {}}})
        with pytest.raises(Exception):
            await client.call_tool("sorftime_call", {"input": {"method": "ProductRequest", "params": {"asin": "B0CVM8TXHP"}}})
        with pytest.raises(Exception):
            await client.call_tool(
                "sorftime_call",
                {"input": {"method": "ProductRequest", "params": {"ASIN": "B0CVM8TXHP", "Unexpected": 1}}},
            )


async def test_shortcut_and_router_share_same_payload_path(settings, fake_client) -> None:
    mcp = create_mcp(settings=settings, client=fake_client, enable_auth=False)

    async with Client(mcp) as client:
        await client.call_tool("product_request", {"input": {"asin": "B0CVM8TXHP", "trend": 1}})
        await client.call_tool(
            "sorftime_call",
            {"input": {"method": "ProductRequest", "params": {"ASIN": "B0CVM8TXHP", "Trend": 1}}},
        )

    assert fake_client.calls[0] == fake_client.calls[1]


async def test_all_safe_methods_have_valid_router_minimal_payloads(settings, fake_client) -> None:
    samples = {
        "CategoryTree": {},
        "CategoryRequest": {"NodeId": "3743561"},
        "CategoryProducts": {"NodeId": "3743561"},
        "CategoryTrend": {"NodeId": "3743561", "TrendIndex": 0},
        "ProductRequest": {"ASIN": "B000000001"},
        "ProductQuery": {"Query": 1, "QueryType": "3", "Pattern": "anker"},
        "AsinSalesVolume": {"ASIN": "B000000001"},
        "ProductVariationHistory": {"ASIN": "B000000001"},
        "ProductRealtimeRequest": {"ASIN": "B000000001"},
        "ProductRealtimeRequestStatusQuery": {"QueryDate": "2024-11-01"},
        "ProductReviewsCollection": {"ASIN": "B000000001", "Mode": 1},
        "ProductReviewsQuery": {"ASIN": "B000000001"},
        "SimilarProductRealtimeRequest": {"Image": "data:image/jpeg;base64,abc"},
        "KeywordQuery": {"PageIndex": 1, "PageSize": 20},
        "KeywordSearchResults": {"Keyword": "power bank"},
        "KeywordRequest": {"Keyword": "power bank"},
        "KeywordSearchResultTrend": {"Keyword": "power bank"},
        "CategoryRequestKeyword": {"NodeId": "3743561"},
        "ASINRequestKeyword": {"ASIN": "B000000001"},
        "KeywordProductRanking": {"Keyword": "power bank"},
        "ASINKeywordRanking": {"ASIN": "B000000001", "Keyword": "power bank"},
        "KeywordExtends": {"Keyword": "power bank"},
        "ProductAssistant": {"Asin": "B000000001", "Type": 0},
        "CategoryAssistant": {"NodeId": "3743561", "Type": 0},
        "AIResultQuery": {"Method": 0},
        "ProductReviewsCollectionStatusQuery": {"ASIN": "B000000001"},
        "SimilarProductRealtimeRequestStatusQuery": {},
        "SimilarProductRealtimeRequestCollection": {"TaskId": "1"},
        "AIResult": {"TaskId": "1"},
        "CoinQuery": {},
        "CoinStream": {"PageIndex": 1, "PageSize": 20},
        "RequestStreamMonth": {},
    }
    assert set(samples) == set(METHOD_REGISTRY)

    mcp = create_mcp(settings=settings, client=fake_client, enable_auth=False)
    async with Client(mcp) as client:
        for method, params in samples.items():
            await client.call_tool("sorftime_call", {"input": {"method": method, "params": params}})

    assert len(fake_client.calls) == len(METHOD_DEFINITIONS)


def test_registry_metadata_is_complete_and_safe() -> None:
    assert not UNSAFE_METHODS.intersection(METHOD_REGISTRY)
    for definition in METHOD_DEFINITIONS:
        assert definition.method
        assert definition.endpoint
        assert definition.category
        assert definition.description
        assert definition.request_cost_note
        assert definition.examples
        assert definition.read_only is True
        assert callable(definition.estimate_cost)


def test_high_frequency_methods_declare_shortcuts() -> None:
    assert HIGH_FREQUENCY_METHODS == {
        "ProductRequest": "product_request",
        "CategoryRequest": "category_request",
        "KeywordRequest": "keyword_request",
        "ProductQuery": "product_query",
        "CategoryTrend": "category_trend",
        "RequestStreamMonth": "request_stream_month",
        "CoinQuery": "coin_query",
    }
    for method, shortcut in HIGH_FREQUENCY_METHODS.items():
        assert METHOD_REGISTRY[method].shortcut_tool == shortcut
