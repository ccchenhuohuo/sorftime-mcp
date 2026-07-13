import { ENDPOINTS } from "../endpoints.js";
import { ValidationError } from "../errors.js";

export type BillingKind = "free" | "request" | "coin" | "recurring_coin" | "unknown";
export type EndpointEffect = "read" | "create" | "update" | "delete";
export type EndpointExposure = "reader" | "admin" | "disabled";

export interface EndpointGovernance {
  billing: BillingKind;
  effect: EndpointEffect;
  exposure: EndpointExposure;
  reason: string;
}

const disabledRead = (billing: BillingKind, reason = "Paid reads are disabled in the initial MCP policy"): EndpointGovernance => ({
  billing, effect: "read", exposure: "disabled", reason,
});
const disabledWrite = (billing: BillingKind, effect: Exclude<EndpointEffect, "read">): EndpointGovernance => ({
  billing, effect, exposure: "disabled", reason: "State-changing and task-creating calls are disabled in the initial MCP policy",
});
const reader = (reason = "Free read-only endpoint approved for governed team access"): EndpointGovernance => ({
  billing: "free", effect: "read", exposure: "reader", reason,
});
const admin = (reason: string): EndpointGovernance => ({ billing: "free", effect: "read", exposure: "admin", reason });

/** Exhaustive machine policy. Never infer authorization from the human-readable `cost` field. */
export const ENDPOINT_GOVERNANCE: Readonly<Record<string, EndpointGovernance>> = {
  CategoryTree: disabledRead("request"),
  CategoryRequest: disabledRead("request"),
  CategoryProducts: disabledRead("request"),
  CategoryTrend: disabledRead("request"),
  ProductRequest: disabledRead("request"),
  ProductQuery: disabledRead("request"),
  AsinSalesVolume: disabledRead("request"),
  ProductVariationHistory: disabledRead("request"),
  ProductRealtimeRequest: disabledWrite("request", "create"),
  ProductRealtimeRequestStatusQuery: disabledRead("request"),
  ProductReviewsCollection: disabledWrite("coin", "create"),
  ProductReviewsCollectionStatusQuery: admin("Existing review-task status is account-level shared data"),
  ProductReviewsQuery: disabledRead("request"),
  SimilarProductRealtimeRequest: disabledWrite("request", "create"),
  SimilarProductRealtimeRequestStatusQuery: admin("Existing image-search task status is account-level shared data"),
  SimilarProductRealtimeRequestCollection: admin("Existing image-search results require an administrator-provided task ID"),
  KeywordQuery: disabledRead("request"),
  KeywordSearchResults: disabledRead("request"),
  KeywordRequest: disabledRead("request"),
  KeywordSearchResultTrend: disabledRead("request"),
  CategoryRequestKeyword: disabledRead("request"),
  ASINRequestKeyword: disabledRead("request"),
  KeywordProductRanking: disabledRead("request"),
  ASINKeywordRanking: disabledRead("request"),
  KeywordExtends: disabledRead("request"),
  FavoriteKeyword: disabledWrite("request", "create"),
  ChangeFavoriteKeyword: disabledWrite("request", "update"),
  GetFavoriteKeyword: disabledRead("unknown", "Undocumented cost and request schema; disabled fail-closed"),
  KeywordBatchSubscription: disabledWrite("recurring_coin", "create"),
  KeywordTasks: reader(),
  KeywordBatchTaskUpdate: disabledWrite("free", "update"),
  KeywordBatchScheduleList: reader(),
  KeywordBatchScheduleDetail: reader(),
  BestSellerListSubscription: disabledWrite("recurring_coin", "create"),
  BestSellerListTask: reader(),
  BestSellerListDelete: disabledWrite("free", "delete"),
  BestSellerListDataCollect: reader(),
  ProductSellerSubscription: disabledWrite("recurring_coin", "create"),
  ProductSellerTasks: admin("Request schema is undocumented; administrator-only experimental read"),
  ProductSellerTaskUpdate: disabledWrite("free", "update"),
  ProductSellerTaskScheduleList: reader(),
  ProductSellerTaskScheduleDetail: reader(),
  ASINSubscription: disabledWrite("recurring_coin", "update"),
  ASINSubscriptionQuery: reader(),
  ASINSubscriptionCollection: reader(),
  ProductAssistant: disabledWrite("request", "create"),
  CategoryAssistant: disabledWrite("request", "create"),
  AIResultQuery: disabledRead("request"),
  AIResult: admin("Existing AI result requires an administrator-provided task ID"),
  CoinQuery: reader("Global shared-account coin balance"),
  CoinStream: admin("Detailed shared-account coin usage may expose operational activity"),
  RequestStreamMonth: reader("Global shared-account request balance and recent usage summary"),
};

export function validateGovernanceCatalog(): void {
  const endpointNames = new Set(ENDPOINTS.map((endpoint) => endpoint.name));
  const policyNames = new Set(Object.keys(ENDPOINT_GOVERNANCE));
  const missing = [...endpointNames].filter((name) => !policyNames.has(name));
  const extra = [...policyNames].filter((name) => !endpointNames.has(name));
  if (missing.length > 0 || extra.length > 0) {
    throw new ValidationError(`Endpoint governance catalog mismatch (missing: ${missing.join(", ") || "none"}; extra: ${extra.join(", ") || "none"}).`);
  }
}

export function governanceFor(endpoint: string): EndpointGovernance {
  const governance = ENDPOINT_GOVERNANCE[endpoint];
  if (!governance) throw new ValidationError(`Endpoint '${endpoint}' has no governance classification.`);
  return governance;
}
