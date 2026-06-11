from dataclasses import dataclass
from datetime import date
from math import ceil
from typing import Callable, Literal

from pydantic import BaseModel

from sorftime_mcp.domains import domains_payload
from sorftime_mcp.models import (
    AIResultInput,
    AIResultQueryInput,
    ASINKeywordRankingInput,
    ASINRequestKeywordInput,
    AsinSalesVolumeInput,
    CategoryAssistantInput,
    CategoryProductsInput,
    CategoryRequestInput,
    CategoryRequestKeywordInput,
    CategoryTrendInput,
    CoinStreamInput,
    KeywordExtendsInput,
    KeywordProductRankingInput,
    KeywordQueryInput,
    KeywordRequestInput,
    KeywordSearchResultTrendInput,
    KeywordSearchResultsInput,
    NoPayloadInput,
    ProductAssistantInput,
    ProductQueryInput,
    ProductRealtimeRequestInput,
    ProductRealtimeRequestStatusQueryInput,
    ProductRequestInput,
    ProductReviewsCollectionInput,
    ProductReviewsCollectionStatusQueryInput,
    ProductReviewsQueryInput,
    ProductVariationHistoryInput,
    SimilarProductRealtimeRequestCollectionInput,
    SimilarProductRealtimeRequestInput,
    SimilarProductRealtimeRequestStatusQueryInput,
    SorftimeCallInput,
    SorftimeInput,
    SorftimeMethodSchemaInput,
    SorftimeMethodsInput,
)

CostEstimator = Callable[[SorftimeInput], int]
PublicToolKind = Literal["methods", "schema", "call", "shortcut"]


@dataclass(frozen=True)
class MethodDefinition:
    method: str
    endpoint: str
    category: str
    input_model: type[SorftimeInput]
    estimate_cost: CostEstimator
    description: str
    request_cost_note: str
    examples: tuple[dict[str, object], ...]
    is_async: bool = False
    read_only: bool = True
    shortcut_tool: str | None = None

    @property
    def required_params(self) -> tuple[str, ...]:
        return model_param_names(self.input_model, required=True)

    @property
    def optional_params(self) -> tuple[str, ...]:
        return model_param_names(self.input_model, required=False)


@dataclass(frozen=True)
class PublicToolDefinition:
    name: str
    kind: PublicToolKind
    description: str
    input_model: type[BaseModel]
    method: str | None = None


def fixed_cost(value: int) -> CostEstimator:
    def estimate_cost(_: SorftimeInput) -> int:
        return value

    return estimate_cost


def _inclusive_days(start: date, end: date) -> int:
    return max((end - start).days + 1, 1)


def estimate_category_request_cost(input_model: SorftimeInput) -> int:
    model = CategoryRequestInput.model_validate(input_model)
    if model.query_start is not None and model.query_date is not None:
        return ceil(_inclusive_days(model.query_start, model.query_date) / 3) * 10
    if model.query_days is not None:
        return ceil(model.query_days / 3) * 10
    return 5


def estimate_product_request_cost(input_model: SorftimeInput) -> int:
    model = ProductRequestInput.model_validate(input_model)
    asin_count = len(model.asin) if isinstance(model.asin, list) else 1
    per_asin = 1
    if (
        model.trend == 1
        and model.query_trend_start_dt is not None
        and model.query_trend_end_dt is not None
        and _inclusive_days(model.query_trend_start_dt, model.query_trend_end_dt) > 15
    ):
        per_asin = 2
    return asin_count * per_asin


def estimate_product_realtime_request_cost(input_model: SorftimeInput) -> int:
    return 2 if input_model.domain == 7 else 1


def estimate_reviews_collection_cost(input_model: SorftimeInput) -> int:
    model = ProductReviewsCollectionInput.model_validate(input_model)
    star_count = 1
    if model.star is not None and model.star.strip() != "":
        star_count = len([item for item in model.star.split(",") if item.strip() != ""])
    page_count = model.page or 1
    return max(star_count, 1) * max(page_count, 1) * 2


def estimate_similar_product_realtime_request_cost(input_model: SorftimeInput) -> int:
    return 6 if input_model.domain == 7 else 5


def model_param_names(input_model: type[SorftimeInput], *, required: bool) -> tuple[str, ...]:
    names: list[str] = []
    for field_name, field_info in input_model.model_fields.items():
        if field_name == "domain":
            continue
        if field_info.is_required() is required:
            names.append(field_info.alias or field_name)
    return tuple(names)


def allowed_param_names(input_model: type[SorftimeInput]) -> set[str]:
    return set(model_param_names(input_model, required=True)) | set(model_param_names(input_model, required=False))


def method_summary(definition: MethodDefinition) -> dict[str, object]:
    return {
        "method": definition.method,
        "endpoint": definition.endpoint,
        "category": definition.category,
        "description": definition.description,
        "requestCost": definition.request_cost_note,
        "async": definition.is_async,
        "readOnly": definition.read_only,
        "shortcutTool": definition.shortcut_tool,
        "required": list(definition.required_params),
        "optional": list(definition.optional_params),
    }


def method_schema(definition: MethodDefinition) -> dict[str, object]:
    return {
        **method_summary(definition),
        "domains": domains_payload(),
        "examples": list(definition.examples),
        "jsonSchema": definition.input_model.model_json_schema(by_alias=True),
    }


def get_method_definition(method: str) -> MethodDefinition:
    if method not in METHOD_REGISTRY:
        allowed = ", ".join(sorted(METHOD_REGISTRY))
        raise ValueError(f"Unsupported Sorftime method: {method}. Allowed methods: {allowed}")
    return METHOD_REGISTRY[method]


def validate_native_params(definition: MethodDefinition, params: dict[str, object]) -> None:
    extra = set(params) - allowed_param_names(definition.input_model)
    if extra:
        allowed = ", ".join(sorted(allowed_param_names(definition.input_model)))
        raise ValueError(f"Unsupported params for {definition.method}: {sorted(extra)}. Allowed params: {allowed}")


def make_model_input(definition: MethodDefinition, *, domain: int, params: dict[str, object]) -> SorftimeInput:
    validate_native_params(definition, params)
    return definition.input_model.model_validate({"domain": domain, **params})


def example(domain: int = 1, **params: object) -> dict[str, object]:
    return {"domain": domain, "params": params}


METHOD_DEFINITIONS: tuple[MethodDefinition, ...] = (
    MethodDefinition("CategoryTree", "CategoryTree", "category", NoPayloadInput, fixed_cost(5), "Get the Amazon category tree.", "5 requests", (example(),)),
    MethodDefinition("CategoryRequest", "CategoryRequest", "category", CategoryRequestInput, estimate_category_request_cost, "Get category Top 100 Best Sellers products.", "5 requests; historical backfill is 10 requests per 3 days rounded up", (example(NodeId="3743561"),), shortcut_tool="category_request"),
    MethodDefinition("CategoryProducts", "CategoryProducts", "category", CategoryProductsInput, fixed_cost(5), "Get more hot-selling products in a category.", "5 requests", (example(NodeId="3743561", Page=1),)),
    MethodDefinition("CategoryTrend", "CategoryTrend", "category", CategoryTrendInput, fixed_cost(5), "Get category market historical trends.", "5 requests", (example(NodeId="3743561", TrendIndex=0),), shortcut_tool="category_trend"),
    MethodDefinition("ProductRequest", "ProductRequest", "product", ProductRequestInput, estimate_product_request_cost, "Get product details and optional trends.", "1 request per ASIN; 2 per ASIN when trend range is over 15 days", (example(ASIN="B0CVM8TXHP", Trend=1),), shortcut_tool="product_request"),
    MethodDefinition("ProductQuery", "ProductQuery", "product", ProductQueryInput, fixed_cost(5), "Search products by Sorftime query conditions.", "5 requests", (example(Page=1, Query=1, QueryType="3", Pattern="anker"),), shortcut_tool="product_query"),
    MethodDefinition("AsinSalesVolume", "AsinSalesVolume", "product", AsinSalesVolumeInput, fixed_cost(1), "Get official ASIN sales volume history.", "1 request", (example(ASIN="B0CVM8TXHP", Page=1),)),
    MethodDefinition("ProductVariationHistory", "ProductVariationHistory", "product", ProductVariationHistoryInput, fixed_cost(1), "Get recent listing variation history.", "1 request", (example(ASIN="B0CVM8TXHP"),)),
    MethodDefinition("ProductRealtimeRequest", "ProductRealtimeRequest", "product", ProductRealtimeRequestInput, estimate_product_realtime_request_cost, "Trigger real-time product collection.", "1 request; JP domain 7 costs 2", (example(ASIN="B0CVM8TXHP", Update=48),), is_async=True),
    MethodDefinition("ProductRealtimeRequestStatusQuery", "ProductRealtimeRequestStatusQuery", "product", ProductRealtimeRequestStatusQueryInput, fixed_cost(1), "Query real-time product collection status.", "1 request", (example(QueryDate="2024-11-01"),)),
    MethodDefinition("ProductReviewsCollection", "ProductReviewsCollection", "product", ProductReviewsCollectionInput, estimate_reviews_collection_cost, "Trigger asynchronous review collection.", "2 coin points per successful 10 reviews; minimum 2", (example(ASIN="B0CVM8TXHP", Mode=1, Star="1,2,5", OnlyPurchase=1, Page=10),), is_async=True),
    MethodDefinition("ProductReviewsQuery", "ProductReviewsQuery", "product", ProductReviewsQueryInput, fixed_cost(5), "Query collected product reviews.", "5 requests", (example(ASIN="B0CVM8TXHP", PageIndex=1),)),
    MethodDefinition("SimilarProductRealtimeRequest", "SimilarProductRealtimeRequest", "product", SimilarProductRealtimeRequestInput, estimate_similar_product_realtime_request_cost, "Trigger image-based similar product search.", "5 requests; JP domain 7 costs 6", (example(Image="data:image/jpeg;base64,..."),), is_async=True),
    MethodDefinition("KeywordQuery", "KeywordQuery", "keyword", KeywordQueryInput, fixed_cost(5), "Query current ABA hot search keywords.", "5 requests", (example(PageIndex=1, PageSize=20),)),
    MethodDefinition("KeywordSearchResults", "KeywordSearchResults", "keyword", KeywordSearchResultsInput, fixed_cost(5), "Get recent search result products for an ABA keyword.", "5 requests", (example(Keyword="power bank", PageIndex=1, PageSize=20),)),
    MethodDefinition("KeywordRequest", "KeywordRequest", "keyword", KeywordRequestInput, fixed_cost(1), "Get keyword details, search volume, and CPC trends.", "1 request", (example(Keyword="power bank"),), shortcut_tool="keyword_request"),
    MethodDefinition("KeywordSearchResultTrend", "KeywordSearchResultTrend", "keyword", KeywordSearchResultTrendInput, fixed_cost(10), "Get trend statistics for keyword search result products.", "10 requests", (example(Keyword="power bank", QueryStart="2024-01", QueryEnd="2025-01"),)),
    MethodDefinition("CategoryRequestKeyword", "CategoryRequestKeyword", "keyword", CategoryRequestKeywordInput, fixed_cost(1), "Reverse-query ABA keywords for a category.", "1 request", (example(NodeId="3743561", PageIndex=1, PageSize=20),)),
    MethodDefinition("ASINRequestKeyword", "ASINRequestKeyword", "keyword", ASINRequestKeywordInput, fixed_cost(1), "Reverse-query keywords for an ASIN.", "1 request", (example(ASIN="B0CVM8TXHP", PageIndex=1, PageSize=20),)),
    MethodDefinition("KeywordProductRanking", "KeywordProductRanking", "keyword", KeywordProductRankingInput, fixed_cost(5), "Get historical monthly keyword search result products.", "5 requests", (example(Keyword="power bank", Month="2024-12", Page=1),)),
    MethodDefinition("ASINKeywordRanking", "ASINKeywordRanking", "keyword", ASINKeywordRankingInput, fixed_cost(2), "Get ASIN ranking trend under a keyword.", "2 requests", (example(Keyword="power bank", ASIN="B07CZDXDG8", QueryStart="2024-12-01", QueryEnd="2025-01-01", Page=1),)),
    MethodDefinition("KeywordExtends", "KeywordExtends", "keyword", KeywordExtendsInput, fixed_cost(5), "Get ABA keyword extensions.", "5 requests", (example(Keyword="power bank", PageIndex=1, PageSize=200),)),
    MethodDefinition("ProductAssistant", "ProductAssistant", "ai", ProductAssistantInput, fixed_cost(25), "Start Sorftime AI product analysis.", "25 requests", (example(Asin="B0CVM8TXHP", Type=0),), is_async=True),
    MethodDefinition("CategoryAssistant", "CategoryAssistant", "ai", CategoryAssistantInput, fixed_cost(25), "Start Sorftime AI category analysis.", "25 requests", (example(NodeId="3743561", Type=0),), is_async=True),
    MethodDefinition("AIResultQuery", "AIResultQuery", "ai", AIResultQueryInput, fixed_cost(1), "Query Sorftime AI task progress.", "1 request", (example(Method=0, Params="B0CVM8TXHP"),)),
    MethodDefinition("ProductReviewsCollectionStatusQuery", "ProductReviewsCollectionStatusQuery", "helper", ProductReviewsCollectionStatusQueryInput, fixed_cost(0), "Query review collection task status.", "0 requests", (example(ASIN="B0CVM8TXHP", Update=48),)),
    MethodDefinition("SimilarProductRealtimeRequestStatusQuery", "SimilarProductRealtimeRequestStatusQuery", "helper", SimilarProductRealtimeRequestStatusQueryInput, fixed_cost(0), "Query image search task status.", "0 requests", (example(Update=48),)),
    MethodDefinition("SimilarProductRealtimeRequestCollection", "SimilarProductRealtimeRequestCollection", "helper", SimilarProductRealtimeRequestCollectionInput, fixed_cost(0), "Get completed image search results.", "0 requests", (example(TaskId="1"),)),
    MethodDefinition("AIResult", "AIResult", "helper", AIResultInput, fixed_cost(0), "Get completed Sorftime AI analysis result.", "0 requests", (example(TaskId="1"),)),
    MethodDefinition("CoinQuery", "CoinQuery", "account", NoPayloadInput, fixed_cost(0), "Get remaining Sorftime coin balance.", "0 requests", (example(),), shortcut_tool="coin_query"),
    MethodDefinition("CoinStream", "CoinStream", "account", CoinStreamInput, fixed_cost(0), "Get Sorftime coin usage records.", "0 requests", (example(PageIndex=1, PageSize=20),)),
    MethodDefinition("RequestStreamMonth", "RequestStreamMonth", "account", NoPayloadInput, fixed_cost(0), "Get monthly request usage summary.", "0 requests", (example(),), shortcut_tool="request_stream_month"),
)

METHOD_REGISTRY = {definition.method: definition for definition in METHOD_DEFINITIONS}

PUBLIC_TOOL_DEFINITIONS: tuple[PublicToolDefinition, ...] = (
    PublicToolDefinition("sorftime_methods", "methods", "List supported Sorftime methods.", SorftimeMethodsInput),
    PublicToolDefinition("sorftime_method_schema", "schema", "Get schema and examples for one Sorftime method.", SorftimeMethodSchemaInput),
    PublicToolDefinition("sorftime_call", "call", "Call any whitelisted read-only Sorftime method.", SorftimeCallInput),
    PublicToolDefinition("product_request", "shortcut", "Shortcut for ProductRequest.", ProductRequestInput, "ProductRequest"),
    PublicToolDefinition("category_request", "shortcut", "Shortcut for CategoryRequest.", CategoryRequestInput, "CategoryRequest"),
    PublicToolDefinition("keyword_request", "shortcut", "Shortcut for KeywordRequest.", KeywordRequestInput, "KeywordRequest"),
    PublicToolDefinition("product_query", "shortcut", "Shortcut for ProductQuery.", ProductQueryInput, "ProductQuery"),
    PublicToolDefinition("category_trend", "shortcut", "Shortcut for CategoryTrend.", CategoryTrendInput, "CategoryTrend"),
    PublicToolDefinition("request_stream_month", "shortcut", "Shortcut for RequestStreamMonth.", NoPayloadInput, "RequestStreamMonth"),
    PublicToolDefinition("coin_query", "shortcut", "Shortcut for CoinQuery.", NoPayloadInput, "CoinQuery"),
)

PUBLIC_TOOL_NAMES = tuple(definition.name for definition in PUBLIC_TOOL_DEFINITIONS)
HIGH_FREQUENCY_METHODS = {
    definition.method: definition.name
    for definition in PUBLIC_TOOL_DEFINITIONS
    if definition.kind == "shortcut" and definition.method is not None
}
UNSAFE_METHODS = {
    "FavoriteKeyword",
    "ChangeFavoriteKeyword",
    "KeywordBatchSubscription",
    "KeywordBatchTaskUpdate",
    "BestSellerListSubscription",
    "BestSellerListDelete",
    "ProductSellerSubscription",
    "ProductSellerTaskUpdate",
    "ASINSubscription",
}
