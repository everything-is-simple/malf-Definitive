# MALF v1.5 Core Definitions and Theorems

日期：2026-05-16

## 1. Core 侧新增对象

v1.5 在 Core 侧新增的不是新 wave 定义，而是对既有结构状态的行为刻画。

### 定义 C1：`continuation_regime`

`continuation_regime` 描述当前 wave 的延续行为 bucket：

```text
advancing
slowing
stalled
transitioning
```

它只能由当前 `system_state`、`new_count`、`no_new_span` 与 rank 类字段派生。

### 定义 C2：`boundary_pressure_regime`

`boundary_pressure_regime` 描述当前结构更靠近哪类边界：

```text
continuation_side
guard_pressure
transition_pressure
neutral
```

它只回答边界关系，不回答买卖方向。

### 定义 C3：`directional_continuity_regime`

`directional_continuity_regime` 描述当前结构表现为：

```text
same_direction_continuation
opposite_direction_rebirth
transition_unresolved
```

它来自 `direction / old_direction / birth_type / system_state`，不来自 PAS 解释。

## 2. Core 定理

1. 行为 bucket 只能基于 MALF 已确认结构事实。
2. `transition` 仍然不是 wave。
3. `wave_behavior_snapshot` 不得让旧 wave 复活。
4. 没有 lineage 的行为 bucket 不得进入正式快照。

## 3. Core 非目标

- 不重定义 `WavePosition`
- 不新增 setup family
- 不新增强弱分值
- 不新增交易动作接口
