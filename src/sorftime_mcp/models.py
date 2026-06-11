from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from sorftime_mcp.domains import DOMAIN_ID_DESCRIPTION


class SorftimeInput(BaseModel):
    """Base model for MCP tool input."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    domain: int = Field(default=1, ge=1, le=14, description=DOMAIN_ID_DESCRIPTION)

    def to_payload(self) -> dict[str, Any]:
        return self.model_dump(
            by_alias=True,
            exclude={"domain"},
            exclude_none=True,
            mode="json",
        )


class NoPayloadInput(SorftimeInput):
    pass


class CategoryRequestInput(SorftimeInput):
    node_id: str = Field(alias="NodeId")
    query_start: date | None = Field(default=None, alias="QueryStart")
    query_date: date | None = Field(default=None, alias="QueryDate")
    query_days: int | None = Field(default=None, ge=1, le=40, alias="QueryDays")


class CategoryProductsInput(SorftimeInput):
    node_id: str = Field(alias="NodeId")
    page: int | None = Field(default=None, ge=1, alias="Page")
    range_limit: int | None = Field(default=None, ge=1, alias="Range")


class CategoryTrendInput(SorftimeInput):
    node_id: str = Field(alias="NodeId")
    trend_index: int = Field(ge=0, le=15, alias="TrendIndex")


class ProductRequestInput(SorftimeInput):
    asin: str | list[str] = Field(alias="ASIN")
    trend: int | None = Field(default=1, ge=1, le=2, alias="Trend")
    query_trend_start_dt: date | None = Field(default=None, alias="QueryTrendStartDt")
    query_trend_end_dt: date | None = Field(default=None, alias="QueryTrendEndDt")

    @field_validator("asin")
    @classmethod
    def validate_asin_count(cls, value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            if value.strip() == "":
                raise ValueError("asin cannot be empty")
            return value
        if not value:
            raise ValueError("asin list cannot be empty")
        if len(value) > 10:
            raise ValueError("ProductRequest supports at most 10 ASINs")
        if any(item.strip() == "" for item in value):
            raise ValueError("asin list cannot contain empty values")
        return value


class ProductQueryInput(SorftimeInput):
    page: int | None = Field(default=None, ge=1, alias="Page")
    query: int | None = Field(default=None, ge=1, le=2, alias="Query")
    query_type: str | None = Field(default=None, alias="QueryType")
    pattern: Any | None = Field(default=None, alias="Pattern")


class AsinSalesVolumeInput(SorftimeInput):
    asin: str = Field(alias="ASIN")
    page: int | None = Field(default=None, ge=1, alias="Page")
    query_date: date | None = Field(default=None, alias="QueryDate")
    query_end_date: date | None = Field(default=None, alias="QueryEndDate")


class ProductVariationHistoryInput(SorftimeInput):
    asin: str = Field(alias="ASIN")


class ProductRealtimeRequestInput(SorftimeInput):
    asin: str = Field(alias="ASIN")
    update: int | None = Field(default=None, ge=1, le=120, alias="Update")


class ProductRealtimeRequestStatusQueryInput(SorftimeInput):
    query_date: date = Field(alias="QueryDate")


class ProductReviewsCollectionInput(SorftimeInput):
    asin: str = Field(alias="ASIN")
    mode: int = Field(ge=0, le=1, alias="Mode")
    star: str | None = Field(default=None, alias="Star")
    only_purchase: int | None = Field(default=None, ge=0, le=1, alias="OnlyPurchase")
    page: int | None = Field(default=None, ge=1, alias="Page")


class ProductReviewsCollectionStatusQueryInput(SorftimeInput):
    asin: str = Field(alias="ASIN")
    update: int | None = Field(default=None, ge=1, le=240, alias="Update")


class ProductReviewsQueryInput(SorftimeInput):
    asin: str = Field(alias="ASIN")
    query_start_dt: date | None = Field(default=None, alias="Querystartdt")
    page_index: int | None = Field(default=None, ge=1, alias="PageIndex")
    star: str | None = Field(default=None, alias="Star")
    only_purchase: int | None = Field(default=None, ge=0, le=1, alias="OnlyPurchase")


class SimilarProductRealtimeRequestInput(SorftimeInput):
    image: str = Field(alias="Image")


class SimilarProductRealtimeRequestStatusQueryInput(SorftimeInput):
    update: int | None = Field(default=None, ge=1, le=240, alias="Update")


class SimilarProductRealtimeRequestCollectionInput(SorftimeInput):
    task_id: str = Field(alias="TaskId")


class KeywordQueryInput(SorftimeInput):
    pattern: dict[str, Any] | None = Field(default=None, alias="Pattern")
    page_index: int | None = Field(default=None, ge=1, alias="PageIndex")
    page_size: int | None = Field(default=None, ge=20, le=200, alias="PageSize")


class KeywordSearchResultsInput(SorftimeInput):
    keyword: str = Field(alias="Keyword")
    page_index: int | None = Field(default=None, ge=1, alias="PageIndex")
    page_size: int | None = Field(default=None, ge=20, le=200, alias="PageSize")


class KeywordRequestInput(SorftimeInput):
    keyword: str = Field(alias="Keyword")


class KeywordSearchResultTrendInput(SorftimeInput):
    keyword: str = Field(alias="Keyword")
    query_start: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$", alias="QueryStart")
    query_end: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$", alias="QueryEnd")


class CategoryRequestKeywordInput(SorftimeInput):
    node_id: str = Field(alias="NodeId")
    page_index: int | None = Field(default=None, ge=1, alias="PageIndex")
    page_size: int | None = Field(default=None, ge=20, le=200, alias="PageSize")


class ASINRequestKeywordInput(SorftimeInput):
    asin: str = Field(alias="ASIN")
    page_index: int | None = Field(default=None, ge=1, alias="PageIndex")
    page_size: int | None = Field(default=None, ge=20, le=200, alias="PageSize")


class KeywordProductRankingInput(SorftimeInput):
    keyword: str = Field(alias="Keyword")
    month: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}$", alias="Month")
    page: int | None = Field(default=None, ge=1, alias="Page")


class ASINKeywordRankingInput(SorftimeInput):
    keyword: str = Field(alias="Keyword")
    asin: str = Field(alias="ASIN")
    query_start: date | None = Field(default=None, alias="QueryStart")
    query_end: date | None = Field(default=None, alias="QueryEnd")
    page: int | None = Field(default=None, ge=1, alias="Page")


class KeywordExtendsInput(SorftimeInput):
    keyword: str = Field(alias="Keyword")
    page_index: int | None = Field(default=None, ge=1, alias="PageIndex")
    page_size: int | None = Field(default=None, ge=20, le=200, alias="PageSize")


class ProductAssistantInput(SorftimeInput):
    asin: str = Field(alias="Asin")
    report_type: int = Field(ge=0, le=1, alias="Type")


class CategoryAssistantInput(SorftimeInput):
    node_id: str = Field(alias="NodeId")
    report_type: int = Field(ge=0, le=1, alias="Type")


class AIResultQueryInput(SorftimeInput):
    method: int = Field(ge=0, le=1, alias="Method")
    params: str | None = Field(default=None, alias="Params")
    query_start: date | None = Field(default=None, alias="QueryStart")
    query_end: date | None = Field(default=None, alias="QueryEnd")


class AIResultInput(SorftimeInput):
    task_id: str = Field(alias="TaskId")


class CoinStreamInput(SorftimeInput):
    query_date: list[date] | None = Field(default=None, min_length=2, max_length=2, alias="QueryDate")
    page_index: int | None = Field(default=None, ge=1, alias="PageIndex")
    page_size: int | None = Field(default=None, ge=20, le=200, alias="PageSize")


class SorftimeMethodsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str | None = Field(default=None, description="Optional method category filter.")


class SorftimeMethodSchemaInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str = Field(description="Sorftime method name, for example ProductRequest.")


class SorftimeCallInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    method: str = Field(description="Whitelisted Sorftime method name.")
    domain: int = Field(default=1, ge=1, le=14, description=DOMAIN_ID_DESCRIPTION)
    params: dict[str, Any] = Field(default_factory=dict, description="Sorftime-native parameter object.")
