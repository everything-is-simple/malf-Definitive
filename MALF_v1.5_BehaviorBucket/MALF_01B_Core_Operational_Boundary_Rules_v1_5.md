# MALF v1.5 Core Operational Boundary Rules

日期：2026-05-16

## 1. 派生顺序

`wave_behavior_snapshot` 的派生顺序固定为：

```text
1. read v1.4 core state
2. read v1.4 lifespan state
3. read transition and birth lineage
4. derive behavior buckets
5. attach audit reasons and rule versions
6. publish read-only snapshot
```

任何跳步都不允许。

## 2. 比较规则

- `transition` 优先于一切延续 bucket。
- 只有在 `system_state != transition` 时，才允许给出 active-wave continuation bucket。
- 没有 `current_effective_guard` 时，不得输出 `guard_pressure`。
- 没有 `confirmation_distance_*` 时，不得输出出生质量 bucket。

## 3. 禁止越界

以下都不允许出现在 v1.5：

- `strength_score`
- `strength_bucket`
- `setup_family`
- `triggered`
- `accepted`
- `rejected`
- `order_intent`
- `profit`

这些都属于 PAS / Signal / Position / Trade 的语义，不属于 MALF。

## 4. 可审计性

每条快照必须带有：

- `source_run_id`
- `malf_v1_4_rule_version`
- `malf_v1_5_rule_version`
- `lineage_hash`
- `reason_codes`

这样 PAS 才能消费结果，而不用回到 `PriceBar` 复读。
