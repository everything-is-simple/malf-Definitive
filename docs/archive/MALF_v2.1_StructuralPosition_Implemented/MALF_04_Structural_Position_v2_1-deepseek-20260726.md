# MALF v2.1 Structural Position — 结构位置

> 层：L1d — Structural Position（结构位置）
>
> 原名：Probability 层（v2.0）。v2.1 重命名，因为该层不输出概率，输出 rank 透传 + 向量差 + 比较标签。
>
> 基于：v2.0 Probability（claude-20260616）
>
> 作者：DeepSeek
>
> 日期：2026-07-26

---

## §0 为什么改名

v2.0 的 "Probability" 层不计算概率。它做三件事：
1. 透传 Lifespan 的 rank 值
2. 计算当前 wave 与最近几波之间的 rank 向量差
3. 对向量差做阈值化，输出标签（accelerating/decelerating/flat 等）

"Probability" 这个名字会制造错误的期待——下游消费者会以为它在输出概率。实际上它输出的是"当前波在历史中的结构位置"。

v2.1 将它重命名为 **Structural Position**（结构位置）。对外快照类型名从 `WaveProbabilitySnapshot` 改为 `WaveStructuralSnapshot`。

**语义不变**：所有字段、计算逻辑、输出格式与 v2.0 完全一致。仅层名和类型名变更。

---

## §1 层职责

Structural Position 层是 MALF 对下游的最终产品。它组合 Core 的结构事实、Range 的震荡特征和 Lifespan 的历史排名，输出四个视图：

- **P1 自身分位**：当前 wave 在历史中的位置
- **P2 同向对照**：当前 wave 与最近同向波的结构位置比较
- **P3 反向对照**：当前 wave 与最近反向波的结构位置比较
- **P4 正反对照**：当前 wave 与最近已终止波的综合比较

---

## §2 Wave 编号约定

MALF 使用以下编号约定引用历史波：

```
W0  = 当前 wave（alive 或刚确认的 new wave）
W-1 = 最近一个已终止的 wave（任意方向）
W-2 = 倒数第二个已终止的 wave
W-3 = 倒数第三个已终止的 wave
...
```

**P2 同向对照**：从 W-1, W-2, W-3 中选取与 W0 同方向的波，取最近 1-3 个。若不足 3 个，有几个用几个；若一个都没有，P2 全为 None。

**P3 反向对照**：从 W-1, W-2, W-3 中选取与 W0 反方向的波，取最近 1-3 个。若不足 3 个，有几个用几个；若一个都没有，P3 全为 None。

**P4 正反对照**：取 W-1（最近一个已终止波，任意方向）。若 W-1 不存在，P4 全为 None。

---

## §3 P1 — 自身分位（Self Rank）

直接透传 Lifespan 的 rank 值，不做任何变换。

> ⚠️ **警告**：P1 输出的是 rank（历史分位），不是概率。rank=0.80 意味着"当前波在历史同类中大于 80% 的波"，不是"有 80% 概率继续涨"。

```
P1:
  span_rank: float | None
  range_rank: float | None
  stagnation_rank: float | None
```

- 当前 wave 为 alive 时：rank 基于 peer_sample（已终止波），当前 wave 不在 peer_sample 中
- 当前 wave 已终止时：rank 计算的 peer_sample 包含当前 wave
- 所有 rank 为 None 时（peer_sample 不足 30）：P1 全为 None

---

## §4 P2 — 同向对照（Same Direction Momentum）

比较当前 wave（W0）与最近 1-3 个同方向已终止波。

> ⚠️ **警告**：P2 输出的是 rank 差（向量差），不是概率。"accelerating" 标签是辅助性的，原始 rank 值始终保留。

### 计算公式

```
peer_waves = W-1, W-2, W-3 中与 W0 同方向的波（取最近 1-3 个）

same_dir_span_momentum = W0.span_rank - mean(peer_waves[].span_rank)
same_dir_range_momentum = W0.range_rank - mean(peer_waves[].range_rank)
same_dir_stagnation_momentum = W0.stagnation_rank - mean(peer_waves[].stagnation_rank)
```

其中 `mean()` 取 peer_waves 中对应 rank 的算术平均。若 peer_waves 为空，所有 momentum 为 None。

### 标签规则

取三个 momentum 的均值 `avg_momentum = (span_momentum + range_momentum + stagnation_momentum) / 3`：

- `avg_momentum > +same_dir_threshold`（默认 0.10）→ `accelerating`
- `avg_momentum < -same_dir_threshold`（默认 0.10）→ `decelerating`
- 其他 → `flat`

```
P2:
  same_dir_span_momentum: float | None
  same_dir_range_momentum: float | None
  same_dir_stagnation_momentum: float | None
  same_dir_label: "accelerating" | "decelerating" | "flat" | None
```

---

## §5 P3 — 反向对照（Opposite Direction Momentum）

比较当前 wave（W0）与最近 1-3 个反方向已终止波。

> ⚠️ **警告**：P3 输出的是 rank 差（向量差），不是概率。"self_dominant" 标签是辅助性的，原始 rank 值始终保留。

### 计算公式

```
peer_waves = W-1, W-2, W-3 中与 W0 反方向的波（取最近 1-3 个）

cross_dir_span_momentum = W0.span_rank - mean(peer_waves[].span_rank)
cross_dir_range_momentum = W0.range_rank - mean(peer_waves[].range_rank)
cross_dir_stagnation_momentum = W0.stagnation_rank - mean(peer_waves[].stagnation_rank)
```

### 标签规则

取三个 momentum 的均值 `avg_momentum = (span_momentum + range_momentum + stagnation_momentum) / 3`：

- `avg_momentum > +cross_threshold`（默认 0.15）→ `self_dominant`
- `avg_momentum < -cross_threshold`（默认 0.15）→ `opposite_dominant`
- 其他 → `balanced`

```
P3:
  cross_dir_span_momentum: float | None
  cross_dir_range_momentum: float | None
  cross_dir_stagnation_momentum: float | None
  cross_dir_label: "self_dominant" | "opposite_dominant" | "balanced" | None
```

---

## §6 P4 — 正反对照（Cross Compare）

比较当前 wave（W0）与最近已终止波（W-1，任意方向）。

> ⚠️ **警告**：P4 输出的是 rank 差（向量差），不是概率。当 `cross_alive_warning = True` 时，P4 的信噪比低于 P2/P3。W0 为 alive 时 rank 不稳定，与已终止的 W-1 的比较是不对称的。

### 计算公式

```
cross_span_momentum = W0.span_rank - W-1.span_rank
cross_range_momentum = W0.range_rank - W-1.range_rank
cross_stagnation_momentum = W0.stagnation_rank - W-1.stagnation_rank
```

若 W-1 不存在，所有 momentum 为 None。

```
P4:
  cross_span_momentum: float | None
  cross_range_momentum: float | None
  cross_stagnation_momentum: float | None
  cross_alive_warning: bool   # True 表示 W0 为 alive，rank 不稳定
```

**P4 噪声警告**：

当 `cross_alive_warning = True`（W0 为 alive）时，W0 的 rank 值会在每根新 bar 后变化。alive wave 的 rank 与已终止波（W-1，rank 已冻结）的比较，本质上是不对称的。P4 在 alive 期间的信号噪声比低于 P2/P3。

下游消费者应结合 `cross_alive_warning` 判断 P4 的可信度。

---

## §7 阈值参数

| 参数 | 默认值 | 用途 | 状态 |
|------|--------|------|------|
| `same_dir_threshold` | 0.10 | P2 标签判定 | 待经验校准 |
| `cross_threshold` | 0.15 | P3 标签判定 | 待经验校准 |
| `peer_sample_min_n` | 30 | 最小样本量 | 统计惯例 |

**关于阈值**：

`same_dir_threshold = 0.10` 和 `cross_threshold = 0.15` 是合理的初始值，但**没有经过经验校准**。它们可能在不同标的、不同周期、不同市场环境下表现不同。

这些阈值是可配置的（`params_default.toml`），但默认值不应被视为"正确值"。建议在引擎跑通真实数据后，通过回测确定合适的阈值范围。

对于不切片哲学的矛盾：这些阈值确实是将连续量（rank 差）切分为离散标签。但标签是辅助性的——原始 rank 值始终保留在输出中。消费者可以忽略标签，直接使用 rank 值。

---

## §8 新标的/新周期退化

当 peer_sample 不足 30 时：
- P1：所有 rank 字段为 None
- P2：所有 momentum 和 label 为 None
- P3：所有 momentum 和 label 为 None
- P4：所有 momentum 为 None，`cross_alive_warning` 仍可用

此时 MALF 退化为纯结构状态机。结构事实（Core）+ 震荡特征（Range）仍然可用。

---

## §9 不变量

| # | 不变量 |
|---|--------|
| P1 | P1 是 Lifespan rank 的透传，不做变换 |
| P2 | P2/P3/P4 的 momentum 是 rank 的向量差，不是概率 |
| P3 | 标签（accelerating 等）是辅助性的，rank 值始终保留 |
| P4 | P4 的 cross_alive_warning 必须真实反映当前 wave 的 alive 状态 |
| P5 | 所有 rank 为 None 时，不 fallback、不补零、不估计 |
| P6 | 阈值可配置，但默认值标注为"待校准" |

---

## §10 测试覆盖要求

### 核心不变量测试（必须覆盖）

| 测试类别 | 最少测试数 | 覆盖内容 |
|---------|----------|---------|
| P1 透传 | 2 | rank 直接透传、rank 为 None 时透传 None |
| P2 同向对照 | 3 | 正常计算、同向 peer 不足、标签判定 |
| P3 反向对照 | 3 | 正常计算、反向 peer 不足、标签判定 |
| P4 正反对照 | 3 | 正常计算、W-1 不存在、alive warning |
| 退化 | 2 | peer_sample 不足 → 全 None、W-1 不存在 → P4 None |

### 边界情况测试（必须覆盖）

| 测试类别 | 最少测试数 |
|---------|----------|
| 所有 rank 为 None | 1 |
| 部分 rank 为 None | 1 |
| 阈值边界（恰好等于 threshold） | 2 |