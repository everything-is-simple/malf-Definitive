# MALF System-Service Interface：语义定稿 v1.3

> v1.4 baseline note: 本文件从 v1.3 继承语义基线；文件内部的 v1.3 表述表示被继承的语义内容。v1.4 的规范增量以 MALF_01B_Core_Operational_Boundary_Rules_v1_4.md 为准。

> 本文件是 `MALF_Three_Part_Design_Set_v1_3` 的 Service 权威定义。  
> Service 只发布 MALF 结构事实与统计位置，不解释机会、不配置资金、不产生订单。  
> v1.3 同步 Core 的 transition boundary 与 Lifespan 的 birth descriptors。

---

## 0. 总述

### 0.0 先读这几句话

Service（服务层）不是新的判断层。它只把 Core 已经确认的结构事实、Lifespan 已经算好的统计位置，整理成 Alpha 能稳定读取的 `WavePosition`。

几个常用词先这样理解：

| 英文术语 | 中文落点 | 人话解释 |
|---|---|---|
| `Service` | 只读服务层 | 只发布，不发明语义 |
| `WavePosition` | 波段位置坐标 | Alpha 读取 MALF 的主入口 |
| `WavePositionLatest` | 最新波段位置 | 每个 symbol/timeframe 的最新一条位置 |
| `transition_trace` | 转换追溯 | break、边界、candidate、confirmation 的来龙去脉 |
| `birth_descriptors` | 出生过程描述 | 新波确认前后的等待、替换、突破距离 |
| `source_run_id` | 来源运行编号 | 这条结果来自哪次构建 |
| `service_version` | 服务接口版本 | 接口形状和字段版本 |

一句话主线：

```text
Service 只读发布 WavePosition；Alpha 可以读，不能写回；MALF 不给买卖和仓位。
```

### 0.1 Service 的定义

MALF-Service 是 MALF 对 Alpha 的稳定只读接口。

```text
Input:
    MALF-Core ledgers
    MALF-Lifespan snapshots

Output:
    WavePosition
    WavePositionLatest
    interface audit
```

Service 不产生新的 Core 语义，不改变 Lifespan 统计结果。

---

## 1. 输入边界

### 定义 S1：Core 输入

Service 可读取以下 Core 事实：

| 输入 | 用途 |
|---|---|
| pivot ledger | H / L 追溯 |
| structure ledger | HH / HL / LL / LH 追溯 |
| wave ledger | wave 创建、方向、终止 |
| break ledger | broken guard 与 break_dt |
| transition ledger | transition boundary |
| candidate ledger | active candidate guard 与 confirmation pivot |

### 定义 S2：Lifespan 输入

Service 可读取以下 Lifespan 事实：

| 输入 | 用途 |
|---|---|
| lifespan snapshot | new_count / no_new_span / ranks |
| lifespan profile | final stats |
| sample version | rank 样本版本 |
| rule version | life-state 阈值版本 |
| birth descriptors | 出生过程描述 |

---

## 2. WavePosition 接口

### 定义 S3：WavePosition

WavePosition 是 Alpha 可读取的 MALF 主接口。

```text
WavePosition =
    identity
    + core_state
    + transition_trace
    + lifespan_stats
    + birth_descriptors
    + versions
```

### 定义 S4：Identity 字段

| 字段 | 含义 |
|---|---|
| symbol | 标的 |
| timeframe | day / week / month |
| bar_dt | 当前 bar 日期 |
| wave_id | 当前 wave |
| service_version | service 接口版本 |

自然键：

```text
symbol + timeframe + bar_dt + service_version
```

### 定义 S5：Core State 字段

| 字段 | 含义 |
|---|---|
| system_state | uninitialized / up_alive / down_alive / transition |
| wave_core_state | alive / terminated |
| direction | up / down；transition 时为 old_direction |
| old_wave_id | transition 时被终止 wave |
| old_direction | transition 时旧 wave 方向 |
| break_dt | break 日期 |

`system_state` 与 `wave_core_state` 必须分开发布，不得混用。

### 定义 S6：Transition Trace 字段

| 字段 | 含义 |
|---|---|
| broken_guard_pivot_id | 被击穿的 current effective guard |
| broken_guard_price | 被击穿的 current effective guard price |
| old_final_progress_extreme_pivot_id | 旧 wave 最终推进极值 pivot |
| old_final_progress_extreme_price | 旧 wave 最终推进极值价格 |
| transition_boundary_high | transition 上边界 |
| transition_boundary_low | transition 下边界 |
| active_candidate_guard_pivot_id | 当前 active candidate guard |
| active_candidate_direction | up / down |
| confirmation_pivot_id | 触发 new wave confirmation 的 pivot |
| confirmed_wave_id | 被确认的新 wave |

这些字段用于解释 new wave 如何被确认，不表示交易建议。

### 定义 S7：Lifespan 字段

| 字段 | 含义 |
|---|---|
| new_count | 推进次数 |
| no_new_span | 未推进持续 bar 数 |
| transition_span | transition 持续 bar 数 |
| update_rank | 推进分位 |
| stagnation_rank | 停滞分位 |
| life_state | early / developing / extended / stagnant / terminal |
| position_quadrant | 二维统计象限 |

### 定义 S8：Birth Descriptor 字段

| 字段 | 含义 |
|---|---|
| birth_type | initial / same-direction / opposite-direction |
| candidate_wait_span | active candidate 到 confirmation 的等待 |
| candidate_replacement_count | transition 内 candidate 替换次数 |
| confirmation_distance_abs | confirmation 突破 boundary 的绝对距离 |
| confirmation_distance_pct | confirmation 突破 boundary 的比例距离 |

Birth descriptor 字段是 v1.3 设计要求，不等于当前实现已落地。

### 定义 S9：Version 字段

| 字段 | 含义 |
|---|---|
| core_rule_version | Core 规则版本 |
| lifespan_rule_version | Lifespan 阈值版本 |
| sample_version | 样本版本 |
| service_version | Service 接口版本 |
| source_run_id | 上游 run id |

---

## 3. WavePositionLatest

### 定义 S10：Latest Surface

WavePositionLatest 是每个 symbol / timeframe 的最新 WavePosition。

```text
WavePositionLatest =
    latest(WavePosition by symbol, timeframe, service_version)
```

Latest surface 只能由 Service 从 WavePosition 派生，不得由 Alpha、Signal 或下游写回。

---

## 4. 禁止输出

### 定义 S11：MALF 非交易接口

MALF-Service 不输出：

```text
buy
sell
weight
order
position_size
portfolio_allocation
target_exposure
```

### 定义 S12：下游只读

Alpha 和所有下游模块只能读取 MALF-Service。

```text
Alpha reads MALF.
Signal reads Alpha.
Position reads Signal.
No downstream module writes back to MALF.
```

---

## 5. 审计规则

### 定义 S13：Source Binding

每一条 WavePosition 必须绑定来源 run。

```text
source_run_id = required
```

### 定义 S14：Natural Key Uniqueness

WavePosition 必须满足自然键唯一。

```text
unique(symbol, timeframe, bar_dt, service_version)
```

### 定义 S15：Transition Boundary Completeness

当 `system_state = transition` 或新 wave 由 transition 确认时，Service 必须能够追溯：

```text
broken_guard_pivot_id
transition_boundary_high
transition_boundary_low
active_candidate_guard_pivot_id
confirmation_pivot_id
```

若实现尚未提供新增字段，必须作为 implementation follow-up 标注，不得伪造。

---

## 6. 定理

### 定理 S-T1：Service 不发明语义

Service 只能发布 Core 和 Lifespan 已产生的事实。

```text
Service semantics = Core semantics + Lifespan semantics
```

### 定理 S-T2：只读接口定理

MALF 对 Alpha 是只读上游。

```text
Alpha may read WavePosition.
Alpha must not write MALF.
```

### 定理 S-T3：交易非输出定理

MALF-Service 不输出交易动作。

```text
WavePosition != buy
WavePosition != sell
WavePosition != weight
WavePosition != order
```

### 定理 S-T4：版本可追溯定理

每条 Service 输出必须可追溯规则版本、样本版本与来源 run。

```text
service_output => core_rule_version + lifespan_rule_version + sample_version + source_run_id
```

---

## 7. 最终句

### 标准版

**MALF-Service 将 Core 的 wave / break / transition / candidate / confirmation 事实与 Lifespan 的 count / span / rank / life-state / birth descriptor 事实合成为 WavePosition，只读发布给 Alpha；Service 不解释价值、不输出交易动作、不允许下游写回。**

### 铁律版

```text
MALF serves structure and position.
Alpha interprets value.
No buy/sell/weight/order from MALF.
No downstream writeback to MALF.
```

