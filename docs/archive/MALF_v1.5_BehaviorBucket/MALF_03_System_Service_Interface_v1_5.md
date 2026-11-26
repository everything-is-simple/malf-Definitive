# MALF v1.5 System Service Interface

日期：2026-05-16

## 1. 服务层定位

Service 仍然不是新的判断层。

它只把 v1.4 已确认结构事实与 v1.5 行为 bucket 整理成只读接口。

## 2. `WaveBehaviorSnapshot`

`WaveBehaviorSnapshot` 是 v1.5 主接口。

它至少包含以下字段组：

| 字段组 | 内容 |
|---|---|
| identity | `symbol / timeframe / bar_dt / service_version` |
| lineage | `source_run_id / lineage_hash / rule_versions` |
| wave linkage | `wave_id / direction / old_wave_id / open_transition_id` |
| continuation | `continuation_regime / directional_continuity_regime` |
| pressure | `stagnation_regime / boundary_pressure_regime` |
| transition | `transition_regime` |
| birth quality | `birth_quality_regime` |
| audit | `reason_codes` |

## 3. `WaveBehaviorSnapshotLatest`

`WaveBehaviorSnapshotLatest` 是每个 `symbol / timeframe` 的最新一条行为快照。

它只能由 `WaveBehaviorSnapshot` 派生，不得被 PAS 或下游写回。

## 4. 服务层铁律

```text
WaveBehaviorSnapshot != strength score
WaveBehaviorSnapshot != setup family
WaveBehaviorSnapshot != accept/reject
WaveBehaviorSnapshot != order/position/fill/profit
```

Service 只读发布行为事实，不发布业务动作。
