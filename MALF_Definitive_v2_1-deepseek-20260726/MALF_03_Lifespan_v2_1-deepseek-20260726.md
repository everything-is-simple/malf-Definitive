# MALF v2.1 Lifespan — 双轨户口与排名

> 层：L1c — Lifespan（生命周期统计）
>
> 基于：v2.0 Lifespan（claude-20260616）+ IMPLEMENTATION-CONTRACT-PATCH L4-1/L4-3
>
> 作者：DeepSeek
>
> 日期：2026-07-26

---

## §1 层职责

Lifespan 层为 Wave 和 Range 建立"户口"——记录每个已终止对象的生命周期指标，并计算其在历史同类中的排名（percentile_rank）。

Lifespan 是"统计层"，不是"判定层"。它不回答"这个波好不好"，只回答"这个波在历史上排第几"。

---

## §2 双轨设计

MALF v2.1 的 Lifespan 是双轨的：

| 轨道 | 对象 | 统计指标 | 排名池 |
|------|------|---------|--------|
| WaveLifespan | 已终止的 Wave | span_bars, price_range, primitive_count, pivot_count | 同方向已终止 Wave |
| RangeLifespan | 已终止的 Range | span_bars, evolution_count, replacement_count, resolution_distance_pct | 同类型 Range（continuation / reversal 分池） |

Wave 和 Range 不混池排名。它们是不同性质的结构对象。

---

## §3 WaveLifespan

### 指标全集

v2.1 的 WaveLifespan 保持 v2.0 的完整指标集，不做简化。以下指标从 Core 的 Wave 对象直接提取：

```
WaveLifespan:
  wave_id: str
  direction: "UP" | "DOWN"
  birth_type: "initial" | "continuation" | "reversal"
  
  # 基础指标（从 Core Wave 提取）
  span_bars: int              # 波段跨度（bar 数）
  price_range: int            # 价格幅度（progress_extreme_price - guard_price 的绝对值）
  primitive_count: int        # 原语数量（wave 内 pivot 相邻配对数）
  pivot_count: int            # pivot 数量（含首个波 pivot）
  progress_pct: float         # 价格推进幅度 / guard 距离的比例
                              #   UP: (progress_extreme_price - first_pivot_price) / (progress_extreme_price - guard_price)
                              #   DOWN: (first_pivot_price - progress_extreme_price) / (guard_price - progress_extreme_price)
  
  # 推进统计（描述波内推进 vs 停滞的关系）
  new_count: int              # 推进 pivot 数量（progress 更新的次数）
  no_new_span: int            # 无新推进的 bar 数（两次 progress 更新之间的 bar 数）
  wave_span_total: int        # 波段总 bar 数（= span_bars，冗余字段用于一致性校验）
  
  # 排名（在 peer_sample 中计算）
  span_rank: float | None     # span_bars 的 percentile_rank
  range_rank: float | None    # price_range 的 percentile_rank
  stagnation_rank: float | None  # span_bars / max(primitive_count, 1) 的 percentile_rank
  progress_rank: float | None # progress_pct 的 percentile_rank
```

### 指标说明

- `new_count`：alive 期间 progress 被更新的次数。new_count 越高，波内推进越频繁。
- `no_new_span`：两次 progress 更新之间的 bar 数累计。no_new_span 越大，波内停滞越久。
- `progress_pct`：推进幅度占总价格区间的比例。接近 1.0 表示几乎无回撤，接近 0.5 表示推进和回撤相当。
- `stagnation_rank` 使用 `span_bars / max(primitive_count, 1)`，即"平均每原语的 bar 数"。值越大表示每个原语跨越的 bar 越多，波内推进越慢（停滞感越强）。

### Peer Sample

```
peer_sample:
  - 同方向（UP 或 DOWN）的已终止 Wave
  - wave 的 termination_bar_dt <= 当前 bar_dt（防前视）
  - 不包含当前 alive wave
```

**约束**：
- 最小样本量 N = 30。若 peer_sample 中同方向已终止 Wave 不足 30 个，所有 rank 字段为 None
- 不 fallback、不补零、不扩展样本范围

**新标的/新周期退化的诚实声明**：

对于新标的或新周期，peer_sample 可能长期为空或不足 30。此时：
- 所有 rank 字段为 None
- 下游 Structural Position 层的 P2-P4 视图全部退化为 None
- MALF 退化为纯结构状态机（只输出 Core 的结构事实）
- 这是诚实的退化，不是 bug

---

## §4 Percentile Rank 公式

### 定义

```
percentile_rank(x, sample) = count(x_i < x) / N
```

其中：
- `x`：当前值
- `sample`：peer_sample 中对应指标的值列表
- `count(x_i < x)`：样本中严格小于 x 的数量
- `N`：样本总数

### 特性

- 范围：[0, 1]（0 表示当前值最小，1 表示当前值最大，不含 1 本身）
- 严格 `<`：等于当前值的样本不计入
- 空样本或 N < 30：返回 None
- 确定性：相同样本 + 相同值 → 相同结果

### 边界情况

| 情况 | 结果 | 说明 |
|------|------|------|
| x 是样本中最小值 | `0.0` | 没有样本值严格小于 x |
| x 是样本中最大值 | `(N-1)/N` | 所有其他样本值都严格小于 x，但 x 自身不计入 |
| 多个样本值等于 x | 不计入 | 严格 `<`，等于的样本不参与 count |
| 样本中所有值都等于 x | `0.0` | 没有严格小于 x 的值 |
| N < 30 | `None` | 样本不足，不计算 |
| sample 为空 | `None` | 无样本，不计算 |
| x 为 None | `None` | 输入无效，不计算 |

**注意**：返回值永远达不到 `1.0`。当 x 是最大值时，返回 `(N-1)/N`，即略小于 1。这是 `percentile_rank` 的标准行为——"大于百分之多少的样本"，不含自身。

---

## §5 RangeLifespan

### 对象

```
RangeLifespan:
  range_id: str
  range_type: "continuation" | "reversal"
  
  # 指标
  span_bars: int
  evolution_count: int
  replacement_count: int
  resolution_distance_pct: float
  
  # 排名（在 peer_sample 中计算）
  span_rank: float | None
  evolution_rank: float | None
  replacement_rank: float | None
  resolution_distance_rank: float | None
```

### Peer Sample

```
peer_sample:
  - 同类型（continuation 或 reversal）的已终止 Range
  - Range 的 resolution_bar_dt <= 当前 bar_dt（防前视）
  - 不包含当前 alive Range（如果存在）
```

约束与 WaveLifespan 一致：最小 N = 30，不足则 None。

---

## §6 Wave ID 生成规则（L4-1）

```
wave_id = "{symbol}_{timeframe}_{sequence_number}"
```

- `symbol`：标的代码（如 "510300"）
- `timeframe`：周期标识（如 "D"）
- `sequence_number`：从 1 开始的递增序号，每次 new wave 确认时 +1
- 永不复用。即使旧的 wave 被废弃，序号也不回退

---

## §7 不变量

| # | 不变量 |
|---|--------|
| L1 | Wave 和 Range 不混池排名 |
| L2 | continuation_range 和 reversal_range 分池 |
| L3 | peer_sample 使用 cutoff <= 当前 bar_dt，防前视 |
| L4 | 最小样本量 N = 30，不足则 None，不 fallback |
| L5 | percentile_rank 使用严格 `<`，不含 `=` |
| L6 | wave_id 永不复用 |
| L7 | 新标的/新周期下 rank 退化为 None，诚实暴露 |

---

## §8 测试覆盖要求

### 核心不变量测试（必须覆盖）

| 测试类别 | 最少测试数 | 覆盖内容 |
|---------|----------|---------|
| WaveLifespan 指标提取 | 3 | span_bars、price_range、progress_pct、new_count、no_new_span |
| RangeLifespan 指标提取 | 2 | span_bars、evolution_count、replacement_count |
| percentile_rank 计算 | 4 | 正常值、最小值、最大值、边界情况 |
| 双轨分池 | 2 | Wave 和 Range 不混池、continuation 和 reversal 分池 |
| 防前视 | 2 | peer_sample 不包含未来 wave、不包含当前 alive wave |
| 样本不足退化 | 2 | N < 30 → None、空样本 → None |

### 边界情况测试（必须覆盖）

| 测试类别 | 最少测试数 |
|---------|----------|
| 全等值样本 | 1 |
| 单样本（N=1） | 1 |
| 大样本（N=1000） | 1 |