import { describe, expect, it } from "vitest";
import { findEndpoint } from "../src/endpoints.js";
import { ValidationError } from "../src/errors.js";
import { buildRequestBody } from "../src/input.js";
import type { EndpointSpec } from "../src/types.js";

function endpoint(name: string): EndpointSpec {
  const value = findEndpoint(name);
  if (!value) throw new Error(`Test fixture endpoint not found: ${name}`);
  return value;
}

describe("request-body coercion", () => {
  it("coerces repeatable/comma-separated ASIN input into an array", async () => {
    await expect(buildRequestBody(endpoint("ProductRequest"), {
      asin: ["B000TEST01,B000TEST02", "B000TEST03"],
      trend: "2",
    })).resolves.toEqual({
      ASIN: ["B000TEST01", "B000TEST02", "B000TEST03"],
      Trend: 2,
    });
  });

  it("coerces integers, JSON objects, and date strings", async () => {
    await expect(buildRequestBody(endpoint("KeywordQuery"), {
      pattern: '{"RankCondition":[1,1000]}',
      pageIndex: "2",
      pageSize: "200",
    })).resolves.toEqual({
      Pattern: { RankCondition: [1, 1000] },
      PageIndex: 2,
      PageSize: 200,
    });

    await expect(buildRequestBody(endpoint("ASINKeywordRanking"), {
      keyword: "sentinel keyword",
      asin: "B000TEST01",
      queryStart: "2026-01-02",
      queryEnd: "2026-02-03",
      page: "1",
    })).resolves.toMatchObject({
      QueryStart: "2026-01-02",
      QueryEnd: "2026-02-03",
      Page: 1,
    });
  });

  it("serializes exact API key casing from normalized CLI properties", async () => {
    await expect(buildRequestBody(endpoint("ProductSellerSubscription"), {
      asin: "B000TEST01",
      checkStock: "1",
      period: "1|1|1",
    })).resolves.toEqual({ Asin: "B000TEST01", CheckStock: 1, Period: "1|1|1" });

    await expect(buildRequestBody(endpoint("ASINSubscription"), {
      asins: "+,B000TEST01,1",
    })).resolves.toEqual({ Asins: "+,B000TEST01,1" });

    await expect(buildRequestBody(endpoint("ProductReviewsQuery"), {
      asin: "B000TEST01",
      querystartdt: "2026-01-02",
    })).resolves.toEqual({ ASIN: "B000TEST01", Querystartdt: "2026-01-02" });
  });

  it("accepts raw JSON, preserves unknown fields, and lets typed options override it", async () => {
    await expect(buildRequestBody(endpoint("CategoryProducts"), {
      data: '{"NodeId":"raw-node","Page":1,"FutureField":"sentinel"}',
      nodeId: "typed-node",
      page: "3",
    })).resolves.toEqual({
      NodeId: "typed-node",
      Page: 3,
      FutureField: "sentinel",
    });
  });

  it("allows raw JSON for endpoints whose typed schema is undocumented", async () => {
    await expect(buildRequestBody(endpoint("ProductSellerTaskUpdate"), {
      data: '{"TaskId":"sentinel-task","Update":1}',
    })).resolves.toEqual({ TaskId: "sentinel-task", Update: 1 });
  });
});

describe("request-body validation", () => {
  it("requires documented required parameters from options or raw JSON", async () => {
    await expect(buildRequestBody(endpoint("CategoryRequest"), {})).rejects.toThrow(
      "Missing required option --node-id",
    );
    await expect(buildRequestBody(endpoint("CategoryRequest"), {
      data: '{"NodeId":"sentinel-node"}',
    })).resolves.toEqual({ NodeId: "sentinel-node" });
  });

  it.each([
    ["CategoryTrend", { nodeId: "sentinel-node", trendIndex: "16" }, "TrendIndex must be at most 15"],
    ["ProductRealtimeRequest", { asin: "B000TEST01", update: "0" }, "Update must be at least 1"],
    ["KeywordBatchTaskUpdate", { taskId: "1", update: "3" }, "Update must be one of: 0, 1, 2, 9"],
    ["KeywordQuery", { pageSize: "19" }, "PageSize must be at least 20"],
  ])("enforces numeric bounds and choices for %s", async (name, options, message) => {
    await expect(buildRequestBody(endpoint(name), options)).rejects.toThrow(message);
  });

  it.each([
    ["CategoryRequest", { nodeId: "sentinel-node", queryStart: "2026-02-30" }, "valid date"],
    ["KeywordSearchResultTrend", { keyword: "sentinel", queryStart: "2026-13" }, "YYYY-MM format"],
    ["BestSellerListDataCollect", {
      nodeId: "sentinel-node",
      bestSellerListType: "5",
      queryDate: "2026-01-01 24",
    }, "YYYY-MM-DD HH format"],
  ])("validates date-like formats for %s", async (name, options, message) => {
    await expect(buildRequestBody(endpoint(name), options)).rejects.toThrow(message);
  });

  it("limits ProductRequest batches to ten ASINs", async () => {
    const asins = Array.from({ length: 11 }, (_, index) => `B000TEST${String(index).padStart(2, "0")}`);
    await expect(buildRequestBody(endpoint("ProductRequest"), { asin: asins })).rejects.toThrow(
      "at most 10 ASINs",
    );
  });

  it("requires both single-condition ProductQuery fields, but permits raw multi-condition input", async () => {
    await expect(buildRequestBody(endpoint("ProductQuery"), { queryType: "3" })).rejects.toThrow(
      "requires --query-type and --pattern",
    );
    await expect(buildRequestBody(endpoint("ProductQuery"), {
      data: '{"Query":2,"Conditions":[{"QueryType":"3","Pattern":"sentinel-brand"}]}',
    })).resolves.toEqual({
      Query: 2,
      Conditions: [{ QueryType: "3", Pattern: "sentinel-brand" }],
    });
  });

  it("requires Area only for desktop keyword monitoring", async () => {
    await expect(buildRequestBody(endpoint("KeywordBatchSubscription"), {
      keyword: "sentinel keyword",
      mode: "0",
    })).rejects.toThrow("requires --area");

    await expect(buildRequestBody(endpoint("KeywordBatchSubscription"), {
      keyword: "sentinel keyword",
      mode: "1",
    })).resolves.toEqual({ Keyword: ["sentinel keyword"], Mode: 1 });
  });

  it("requires exactly two CoinStream dates", async () => {
    await expect(buildRequestBody(endpoint("CoinStream"), {
      queryDate: "2026-01-01",
    })).rejects.toThrow("requires exactly two values");

    await expect(buildRequestBody(endpoint("CoinStream"), {
      queryDate: ["2026-01-01", "2026-06-01"],
    })).resolves.toEqual({ QueryDate: ["2026-01-01", "2026-06-01"] });
  });

  it("requires a ProductRequest trend start when an end is provided", async () => {
    await expect(buildRequestBody(endpoint("ProductRequest"), {
      asin: "B000TEST01",
      queryTrendEndDt: "2026-02-01",
    })).rejects.toThrow("requires --query-trend-start-dt");
  });

  it("rejects conflicting raw input modes and non-object JSON", async () => {
    await expect(buildRequestBody(endpoint("CoinQuery"), {
      data: "{}",
      dataFile: "/tmp/sentinel-never-read.json",
    })).rejects.toThrow("Use only one of --data, --data-file, or --stdin");

    await expect(buildRequestBody(endpoint("CoinQuery"), { data: "[]" })).rejects.toThrow(
      "must contain a JSON object",
    );
    await expect(buildRequestBody(endpoint("CoinQuery"), { data: "{" })).rejects.toBeInstanceOf(ValidationError);
  });
});
