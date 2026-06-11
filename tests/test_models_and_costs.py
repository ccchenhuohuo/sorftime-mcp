from datetime import date

import pytest
from pydantic import ValidationError

from sorftime_mcp.audit import sanitize_for_audit
from sorftime_mcp.catalog import (
    estimate_category_request_cost,
    estimate_product_realtime_request_cost,
    estimate_product_request_cost,
    estimate_reviews_collection_cost,
    estimate_similar_product_realtime_request_cost,
)
from sorftime_mcp.models import (
    AIResultInput,
    ASINKeywordRankingInput,
    ASINRequestKeywordInput,
    CategoryRequestInput,
    CategoryRequestKeywordInput,
    KeywordRequestInput,
    ProductRealtimeRequestInput,
    ProductRequestInput,
    ProductReviewsCollectionInput,
    SimilarProductRealtimeRequestInput,
)


def test_payload_uses_sorftime_field_names() -> None:
    input_model = CategoryRequestInput(
        node_id="3743561",
        query_start=date(2024, 1, 1),
        query_date=date(2024, 1, 10),
    )

    assert input_model.to_payload() == {
        "NodeId": "3743561",
        "QueryStart": "2024-01-01",
        "QueryDate": "2024-01-10",
    }


def test_input_validation_rejects_invalid_domain() -> None:
    with pytest.raises(ValidationError):
        CategoryRequestInput(node_id="3743561", domain=15)


def test_product_request_rejects_too_many_asins() -> None:
    with pytest.raises(ValidationError):
        ProductRequestInput(asin=[f"B00000000{i}" for i in range(11)])


@pytest.mark.parametrize(
    ("input_model", "payload"),
    [
        (CategoryRequestInput, {"NodeId": ""}),
        (KeywordRequestInput, {"Keyword": "   "}),
        (ASINRequestKeywordInput, {"ASIN": ""}),
        (ASINKeywordRankingInput, {"ASIN": "B000000001", "Keyword": ""}),
        (CategoryRequestKeywordInput, {"NodeId": ""}),
        (AIResultInput, {"TaskId": ""}),
        (SimilarProductRealtimeRequestInput, {"Image": ""}),
    ],
)
def test_required_strings_reject_empty_values(input_model, payload) -> None:
    with pytest.raises(ValidationError):
        input_model.model_validate(payload)


def test_required_strings_are_stripped() -> None:
    input_model = KeywordRequestInput(Keyword="  power bank  ")

    assert input_model.to_payload() == {"Keyword": "power bank"}


def test_request_cost_estimators() -> None:
    assert estimate_category_request_cost(CategoryRequestInput(node_id="1")) == 5
    assert estimate_category_request_cost(CategoryRequestInput(node_id="1", query_days=7)) == 30
    assert estimate_product_request_cost(ProductRequestInput(asin=["B000000001", "B000000002"])) == 2
    assert (
        estimate_product_request_cost(
            ProductRequestInput(
                asin="B000000001",
                trend=1,
                query_trend_start_dt=date(2024, 1, 1),
                query_trend_end_dt=date(2024, 1, 20),
            )
        )
        == 2
    )
    assert estimate_product_realtime_request_cost(ProductRealtimeRequestInput(asin="B000000001", domain=7)) == 2
    assert (
        estimate_similar_product_realtime_request_cost(
            SimilarProductRealtimeRequestInput(image="data:image/jpeg;base64,aaa", domain=7)
        )
        == 6
    )
    assert estimate_reviews_collection_cost(ProductReviewsCollectionInput(asin="B000000001", mode=1, star="1,2", page=3)) == 12


def test_audit_sanitizer_redacts_secrets_and_summarizes_images() -> None:
    sanitized = sanitize_for_audit(
        {
            "Authorization": "BasicAuth secret",
            "Image": "x" * 250,
            "nested": {"api_key": "secret"},
        }
    )

    assert sanitized["Authorization"] == "[REDACTED]"
    assert sanitized["nested"]["api_key"] == "[REDACTED]"
    assert "[truncated:250]" in sanitized["Image"]
