# Governed workflows

## Keyword monitoring

1. Ask for marketplace and a keyword/task selector.
2. Call `sorftime_list_monitors` with `monitorType="keyword_ranking"`.
3. If multiple tasks match, present identifiers and wait for selection.
4. Call `sorftime_get_monitoring_results` with `resultType="keyword_runs"` and the selected TaskId.
5. Ask which batch to inspect unless the user already named one.
6. Call `resultType="keyword_run_data"` with exact ScheduleId values.
7. Describe observed rank/result-list changes; do not infer advertising, demand, or competitor causality.

## Best Seller monitoring

1. List monitors with `monitorType="best_seller"` when NodeId/list type is unknown.
2. Confirm marketplace, NodeId, list type, and exact `YYYY-MM-DD HH` snapshot time.
3. Call `resultType="best_seller_data"`.
4. Preserve the source timestamp. The monitor schedule is documented in Beijing time; do not silently convert an ambiguous hour.

## Seller and stock monitoring

1. A reader must already have TaskId/ScheduleId; listing seller tasks is admin-only until its upstream schema is verified.
2. Call `seller_runs`, then `seller_run_data` after a batch is selected.
3. Treat monitor time as the marketplace-local timezone unless the returned payload states otherwise.
4. Report observed sellers/stock only. Do not claim total Amazon inventory or seller intent.

## ASIN subscriptions

1. List `asin_subscription` monitors when active subscription membership is unknown.
2. Confirm each ASIN has exactly 10 uppercase letters/digits.
3. Call `asin_subscription_data` for at most 100 ASINs.
4. If an ASIN is not active or no data is returned, say it is unavailable in shared subscriptions. Never fall back to paid `ProductRequest`.

## Quota

1. Call `sorftime_check_quota` once.
2. Explain that Coin and Request balances belong to the shared account.
3. Do not infer per-person usage from a global balance. Per-person MCP calls are available only in the service audit log to administrators.

## Requests outside policy

For realtime products, product search, category research, keyword research, task creation, update, pause, resume, or deletion:

1. Do not call a vaguely related free tool.
2. State that the initial MCP policy does not expose paid or state-changing operations.
3. Offer explicitly dated existing monitoring/subscription data only if it answers a narrower question.
4. Otherwise direct the user to an administrator, who may use the CLI under separate operational controls.
