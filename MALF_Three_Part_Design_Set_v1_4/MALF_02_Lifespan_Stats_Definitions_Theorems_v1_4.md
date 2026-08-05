# MALF-Lifespan-Stats 波段统计学定义：语义定稿 v1.3

> v1.4 baseline note: 本文件从 v1.3 继承语义基线；文件内部的 v1.3 表述表示被继承的语义内容。v1.4 的规范增量以 MALF_01B_Core_Operational_Boundary_Rules_v1_4.md 为准。

> 本文件是 `MALF_Three_Part_Design_Set_v1_3` 的 Lifespan 权威定义。  
> Lifespan 建立在 MALF-Core 已确认 wave 之上，只描述生命统计位置，不确认 wave 是否成立。  
> v1.3 增加 birth descriptors，用于描述新生命形成过程，但不输出预测或交易信号。

---

## 0. 总述

### 0.0 先读这几句话

Lifespan（生命统计层）不负责判断波段是否成立。这个问题已经由 Core 回答。Lifespan 只看一条已经确认的 wave，现在推进了多少次、多久没有推进、在同类历史样本里处在什么位置。

几个常用词先这样理解：

| 英文术语 | 中文落点 | 人话解释 |
|---|---|---|
| `new_count` | 推进次数 | up 数 HH，down 数 LL |
| `no_new_span` | 未推进持续时间 | 距离上一次 HH/LL 推进过了多少 bar |
| `peer_sample` | 同类样本 | 拿来比较的历史同类 wave |
| `rank` | 历史分位位置 | 当前 wave 在同类样本里的排位，不是概率 |
| `life_state` | 生命状态 | early / developing / extended / stagnant / terminal |
| `position_quadrant` | 二维位置象限 | 推进强弱和停滞强弱的组合 |
| `birth descriptors` | 出生过程描述 | 新波从 transition 里形成时的等待、替换、突破距离 |
| `WavePosition` | 波段位置坐标 | 给 Alpha 读取的稳定坐标 |

一句话主线：

```text
Core 确认 wave -> Lifespan 数推进和停滞 -> 放入同类样本比较 -> 输出 WavePosition
```

### 0.1 Lifespan-Stats 的定义

**MALF-Lifespan-Stats 是建立在 MALF-Core 已确认 wave 之上的统计层：它以 progress primitive 的更新次数定义 new-count，以 progress primitive 未更新的持续时间定义 no-new-span，以历史同类样本定义统计分位，并把 wave 映射为 WavePosition。**

压缩表达：

```text
MALF-Lifespan-Stats = Wave -> Count -> Span -> Sample -> Rank -> Position
```

v1.3 增加：

```text
Birth Description = transition_span + candidate history + confirmation distance
```

Birth Description 只描述形成过程，不预测未来收益。

---

## 1. 基础定义

### 定义 L1：统计对象

Lifespan 的统计对象必须是 MALF-Core 已确认的 wave。

```text
Input = confirmed wave from MALF-Core
```

Transition 不是 wave，因此 transition 本身不产生 new_count 或 no_new_span。

### 定义 L2：Progress Primitive

Progress Primitive 是当前 wave 方向上的推进原语。

| wave direction | progress primitive |
|---|---|
| up | HH |
| down | LL |

HL / LH 是 guard primitive，不增加 new-count。

### 定义 L3：New-count

New-count 是一个 wave 生命周期内 progress primitive 被确认更新的累计次数。

```text
new_count(wave, t) = count(progress_update <= t)
```

| wave direction | counted primitive |
|---|---|
| up | HH only |
| down | LL only |

### 定义 L4：No-new-span

No-new-span 是自上一次 progress primitive 更新以来经过的 bar 数。

```text
no_new_span(wave, t) = bars_since_last_progress_update
```

| 当前 bar 事件 | no_new_span |
|---|---|
| new wave confirmation bar | 0 |
| progress primitive 更新 | 0 |
| 无 progress update 且 wave alive | previous + 1 |
| wave terminated | freeze |

### 定义 L5：New Wave 起点

New wave 被 Core 确认的 bar 必然包含 progress confirmation，因此：

```text
new_count = 1
no_new_span = 0
```

Transition 期间经过的 bar 数不计入 new wave 的 no-new-span。

```text
transition_span != no_new_span(new_wave)
```

### 定义 L6：终止冻结

Wave terminated 时，Lifespan 冻结其最终统计状态。

| 字段 | 含义 |
|---|---|
| final_new_count | 终止时 new-count |
| final_no_new_span | 终止时 no-new-span |
| final_update_rank | 终止时 update-rank |
| final_stagnation_rank | 终止时 stagnation-rank |

---

## 2. 同类样本与 Rank

### 定义 L7：同类样本

同类样本是用于比较当前 wave 的历史 wave 集合。

默认最小 sample scope：

| 维度 | 默认值 |
|---|---|
| timeframe | 当前 timeframe |
| direction | 当前 wave direction |
| universe | 全市场合格标的池 |
| birth_type | all，可配置 |
| sample_cutoff | 不晚于当前 bar_dt |
| sample_version | 必须指定 |

### 定义 L8：Update-rank

Update-rank 是当前 wave 的 new-count 在同类样本中的分位位置。

```text
update_rank = percentile_rank(new_count, peer_sample)
```

### 定义 L9：Stagnation-rank

Stagnation-rank 是当前 wave 的 no-new-span 在同类样本中的分位位置。

```text
stagnation_rank = percentile_rank(no_new_span, peer_sample)
```

### 定义 L10：Rule Version

Lifespan 的阈值必须版本化。

```text
lifespan_rule_version = required
```

阈值不是 Core 语义的一部分，不得反向改变 Core wave 是否成立。

---

## 3. Life State 与 Position Quadrant

### 定义 L11：Life-state

Life-state 是根据 update-rank、stagnation-rank 与 wave_core_state 得到的统计状态。

```text
life_state ∈ {
    early,
    developing,
    extended,
    stagnant,
    terminal
}
```

判定顺序：

| 顺序 | 条件 | life_state |
|---:|---|---|
| 1 | wave_core_state = terminated | terminal |
| 2 | stagnation_rank >= high_stagnation_threshold | stagnant |
| 3 | update_rank >= high_update_threshold | extended |
| 4 | update_rank < low_update_threshold | early |
| 5 | 其它 | developing |

### 定义 L12：Position Quadrant

Position Quadrant 用于保留 update-rank 与 stagnation-rank 的二维组合，不替代 life-state。

| update-rank | stagnation-rank | position_quadrant |
|---:|---:|---|
| 低 | 低 | early_active |
| 高 | 低 | extended_active |
| 低 | 高 | early_stagnant |
| 高 | 高 | extended_stagnant |
| 中间区 | 中间区 | developing |

---

## 4. Birth Descriptors

### 定义 L13：Birth Type

Birth Type 描述 new wave 的出生方向关系。

```text
birth_type ∈ {
    initial,
    same_direction_after_break,
    opposite_direction_after_break
}
```

### 定义 L14：Transition-span

Transition-span 描述 break 后到 new wave confirmed 前 transition 持续的 bar 数。

```text
transition_span = bars_between(break_dt, new_wave_confirmed_dt)
```

Transition-span 属于出生过程描述，不属于 new wave 的 no-new-span。

### 定义 L15：Candidate Wait Span

Candidate Wait Span 描述 active candidate guard 出现后，到 progress confirmation 发生前等待的 bar 数。

```text
candidate_wait_span =
    bars_between(active_candidate_guard_dt, progress_confirmation_dt)
```

### 定义 L16：Candidate Replacement Count

Candidate Replacement Count 描述同一 transition 中 active candidate 被相反方向 candidate guard 替换的次数。

```text
candidate_replacement_count =
    count(candidate_guard invalidations inside transition)
```

### 定义 L17：Confirmation Distance

Confirmation Distance 描述 progress confirmation 突破 transition boundary 的距离。

```text
confirmation_distance_abs(up) =
    confirmation_H_price - transition_boundary_high

confirmation_distance_abs(down) =
    transition_boundary_low - confirmation_L_price
```

```text
confirmation_distance_pct =
    confirmation_distance_abs / boundary_reference_price
```

Confirmation Distance 只描述出生时越过边界的幅度，不表示未来收益概率。

---

## 5. WavePosition

### 定义 L18：WavePosition

WavePosition 是 Lifespan 输出给 Alpha 的主坐标。

```text
WavePosition =
    system_state
    + wave_core_state
    + direction
    + new_count
    + no_new_span
    + update_rank
    + stagnation_rank
    + life_state
    + position_quadrant
    + birth descriptors
```

最小字段：

| 字段 | 含义 |
|---|---|
| symbol | 标的 |
| timeframe | day / week / month |
| bar_dt | 当前 bar 日期 |
| wave_id | 当前 wave |
| old_wave_id | transition 时被终止 wave |
| system_state | uninitialized / up_alive / down_alive / transition |
| wave_core_state | alive / terminated |
| direction | up / down；transition 时保留 old_direction |
| new_count | 推进次数 |
| no_new_span | 未推进持续 bar 数 |
| transition_span | transition 已持续 bar 数 |
| update_rank | 推进分位 |
| stagnation_rank | 停滞分位 |
| life_state | early / developing / extended / stagnant / terminal |
| position_quadrant | 二维统计象限 |
| birth_type | initial / same-direction / opposite-direction |
| candidate_wait_span | active candidate 等待 confirmation 的 bar 数 |
| candidate_replacement_count | transition 内 candidate 替换次数 |
| confirmation_distance_abs | 出生 confirmation 突破边界的绝对距离 |
| confirmation_distance_pct | 出生 confirmation 突破边界的比例距离 |
| sample_scope | 样本范围 |
| sample_version | 样本版本 |
| lifespan_rule_version | life-state 阈值版本 |

新增 birth descriptor 字段为 v1.3 设计要求，不等于当前实现已落地。

---

## 6. 定理

### 定理 L-T1：推进唯一计数定理

New-count 只能由 progress primitive 更新产生。

```text
new_count(up wave)   counts HH only
new_count(down wave) counts LL only
```

### 定理 L-T2：无推进累积定理

当 wave alive 且没有 progress update：

```text
no_new_span = previous_no_new_span + 1
```

若发生 progress update：

```text
no_new_span = 0
```

### 定理 L-T3：初始归零定理

New wave confirmation bar 的 no-new-span 必须为 0。

```text
new_wave.confirmed => no_new_span = 0
```

Transition-span 不并入 no-new-span。

### 定理 L-T4：Break 冻结定理

Break 发生后，旧 wave 的 Lifespan 统计冻结。

```text
break => freeze(new_count, no_new_span, ranks)
```

### 定理 L-T5：Transition 方向保留定理

当 `system_state = transition` 时，WavePosition 必须保留 old_direction。

```text
system_state = transition => direction = old_direction
```

### 定理 L-T6：Rank 非预测定理

Rank 只表示历史位置，不表示未来收益概率。

```text
rank != probability
rank != expected_return
rank != trading_signal
```

### 定理 L-T7：Birth Descriptor 非预测定理

Birth descriptors 只描述出生过程，不表示未来收益、交易胜率或买卖建议。

```text
birth_descriptor != probability
birth_descriptor != expected_return
birth_descriptor != trading_signal
```

### 定理 L-T8：WavePosition 完备定理

对 Alpha 而言，一个 wave 的最小统计位置由以下字段构成：

```text
system_state
wave_core_state
direction
new_count
no_new_span
update_rank
stagnation_rank
life_state
position_quadrant
```

v1.3 的出生过程补充坐标由 birth descriptors 构成。

---

## 7. 最终句

### 标准版

**MALF-Lifespan-Stats 在 MALF-Core 已确认 wave 之上，统计其推进次数、未推进持续时间、transition 等待、candidate 替换与 confirmation 距离，并将这些统计量置入版本化的历史同类样本中，得到 update-rank、stagnation-rank、life-state、position_quadrant、birth descriptors 与 WavePosition；当系统处于 transition 时，WavePosition 必须保留 old_direction。**

### 铁律版

```text
Rank is position, not prediction.
Birth describes formation, not outcome.
Transition keeps old direction.
```

