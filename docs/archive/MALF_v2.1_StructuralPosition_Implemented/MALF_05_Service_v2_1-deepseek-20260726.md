# MALF v2.1 Service — 对外接口与铁律

> 层：L2 — Service（对外接口）
>
> 基于：v2.0 Service（claude-20260616）+ IMPLEMENTATION-CONTRACT-PATCH S-01
>
> 作者：DeepSeek
>
> 日期：2026-07-26

---

## §1 层职责

Service 层是 MALF 的对外边界。它定义：
- 唯一对外契约：`WaveStructuralSnapshot`（v2.1 重命名，原 `WaveProbabilitySnapshot`）
- 快照的完整结构（组合 Core + Range + Lifespan + Structural Position）
- 发布规则、持久化规则、版本规则
- 下游不准逾越的六条铁律（S6）

---

## §2 WaveStructuralSnapshot — 唯一对外契约

```
WaveStructuralSnapshot:
  # 标识
  symbol: str                    # 标的代码
  timeframe: str                 # 周期（"D"）
  bar_dt: datetime               # 当前 bar 时间戳
  bar_index: int                 # 当前 bar 序号
  
  # Core 层
  system_state: str              # "UP_ALIVE" | "DOWN_ALIVE" | "TRANSITION" | "UNINITIALIZED"
  direction: str | None          # "UP" | "DOWN" | None
  active_wave_id: str | None     # 当前 alive wave 的 ID
  progress_extreme_price: int | None
  progress_extreme_bar_dt: datetime | None
  guard_price: int | None
  guard_bar_dt: datetime | None
  bar_count: int | None          # 当前 wave 的 bar 数（transition 期间为 None）
  break_bar_dt: datetime | None
  break_price: int | None
  
  # Transition / Range 层
  transition_boundary_high: int | None
  transition_boundary_low: int | None
  candidate_pivot_type: str | None
  candidate_pivot_price: int | None
  range_boundary_high_now: int | None
  range_boundary_low_now: int | None
  range_evolution_count: int | None
  range_candidate_replacement_count: int | None
  range_type: str | None         # "continuation" | "reversal" | None
  
  # Lifespan 层（Wave）
  wave_span_rank: float | None
  wave_range_rank: float | None
  wave_stagnation_rank: float | None
  
  # Lifespan 层（Range）
  range_span_rank: float | None
  range_evolution_rank: float | None
  range_replacement_rank: float | None
  range_resolution_distance_rank: float | None
  
  # Structural Position 层
  p2_same_dir_span_momentum: float | None
  p2_same_dir_range_momentum: float | None
  p2_same_dir_label: str | None
  p3_cross_dir_span_momentum: float | None
  p3_cross_dir_range_momentum: float | None
  p3_cross_dir_label: str | None
  p4_cross_span_momentum: float | None
  p4_cross_range_momentum: float | None
  p4_cross_alive_warning: bool
  
  # 元数据
  rule_versions: dict[str, str]  # 参与计算的规则版本
  lineage_hash: str | None       # 计算链路哈希
  reason_codes: list[str]        # 字段为 None 的原因代码
  usage: str                     # "research_only" | "verification_only" | "rejected"
  freshness: str                 # "stale_research_only" 等
```

---

## §3 发布规则

### 不可变发布

快照一旦生成，不可修改。发布采用不可变 snapshot 机制：
- 每根 bar 产生一个快照
- 快照写入 `var/published/` 目录
- `var/current.json` 为原子指针，指向最新快照
- 禁止静默回退。回退必须显式、可审计

### 用途降级

```
usage:
  - "research_only"      # 数据过期或模型不完整时
  - "verification_only"   # 用于验证
  - "rejected"            # 输入完整性失败
  - "operational"         # v0.1 禁用，需未来独立审批
```

### usage 判定规则

| usage | 触发条件 | 下游是否可消费 |
|-------|---------|--------------|
| `rejected` | G0 输入完整性失败（结构性坏记录、整只标的拒绝） | 不可消费。快照仅用于审计记录 |
| `research_only` | G1 数据合同不满足（peer_sample < 30、数据过期、freshness = stale）或 G2 模型不完整（rank 字段为 None） | 仅研究。不进 Signal、不进决策、不展示为"当前状态" |
| `verification_only` | 回测验证模式。数据完整但用途受限（如 adapter 为 research variant） | 仅验证。可比较历史结果，但不可作为"当前风险状态" |
| `operational` | G0 + G1 + G2 + G3 全部通过 + 独立审批 | **v0.1 禁用**。需未来独立审批后方可启用 |

**判定优先级**：rejected > research_only > verification_only > operational。一旦满足 rejected 的条件，不再降级为 research_only。

---

## §4 持久化规则

### var/ 目录（可重建）

```
var/
├── staging/       # 中间计算产物
├── published/     # 不可变快照
└── current.json   # 原子指针
```

- `var/` 只保存可删除、可重建的派生数据
- 不进入 Git
- 删除或重建 `var/` 不得触碰 `state/`

### 快照序列化格式

v0.1 快照使用 JSON Lines（`.jsonl`）格式存储：

```
var/published/{symbol}/{timeframe}/{symbol}_{timeframe}_{bar_dt}.jsonl
```

每行一个完整的 JSON 快照对象。选择理由：
- 人类可读（便于审计和调试）
- 逐行追加（不可变，不需重写整个文件）
- 与 `current.json` 原子指针兼容

未来版本可在保持兼容的前提下迁移到 Parquet 或 DuckDB 以提升查询性能。

### 批量查询策略

- 按 `symbol + timeframe + bar_dt` 索引
- 历史快照按年月归档：`var/published/{symbol}/{timeframe}/archive/{YYYY}/{MM}/`
- `current.json` 始终指向最新快照的完整路径

### 中断恢复（S-01）

若计算中断（如进程崩溃），恢复策略：
1. 从 `var/current.json` 读取最后一个成功发布的快照
2. 从该快照的 `bar_dt` 之后重新开始计算
3. 中断前的快照不重算、不覆盖
4. 恢复后 `var/current.json` 原子更新为最新快照

---

## §5 版本规则

### rule_versions

每个快照记录所有参与计算的规则版本：

```
rule_versions:
  pivot_rule: "fractal_k2_v1.0"
  price_domain: "source_integer_fixed_point_v0.1"
  adapter: "malf-v2.1-etf-tick-v0.1"
  core_version: "v2.1"
  range_version: "v2.1"
  lifespan_version: "v2.1"
  structural_position_version: "v2.1"
```

### lineage_hash

计算链路哈希：从输入 bars 到最终快照的完整计算路径的哈希值。用于审计和 replay 验证。

---

## §6 S6 铁律

### 铁律 1：唯一对外契约

`WaveStructuralSnapshot` 是 MALF 对下游的唯一契约。下游不直接访问 Core、Range、Lifespan 或 Structural Position 的内部对象。

### 铁律 2：下游不准写回

下游消费者只能读取快照，不能修改快照的任何字段。快照是只读的。

### 铁律 3：快照只读

快照一旦发布，不可原地修改。如需修正，发布新快照并记录修正原因。

### 铁律 4：None 不准 fallback

字段为 None 时，下游不准用 0、-1、默认值或其他任意值填充。None 就是 None，必须向用户展示为"未形成"。

### 铁律 5：rule_versions 完整记录

每个快照必须包含完整的 `rule_versions` 字典。缺少任何参与计算的规则版本，快照不得发布。

### 铁律 6：reason_codes 必附

任何为 None 的字段必须在 `reason_codes` 中说明原因。示例：
- `"peer_sample_insufficient"`：样本不足 30
- `"wave_alive"`：当前 wave 未终止，rank 不可用
- `"transition_active"`：transition 期间 bar_count 为 None
- `"uninitialized"`：数据不足，尚未初始化

---

## §7 不变量

| # | 不变量 |
|---|--------|
| S1 | WaveStructuralSnapshot 是唯一对外契约 |
| S2 | 快照不可变，下游不可写回 |
| S3 | None 不准 fallback，必须附 reason_codes |
| S4 | rule_versions 必须完整 |
| S5 | 发布采用不可变 snapshot，禁止静默回退 |
| S6 | var/ 可重建，state/ 不可重建 |

---

## §8 失败模式与退化

MALF 在以下场景中会退化。退化是**确定性的、可预期的**，不是 bug。

### 失败模式枚举

| 场景 | 触发条件 | 快照表现 | reason_codes |
|------|---------|---------|-------------|
| **Core 未初始化** | bar 序列不足 k+2 根，尚未检测到 pivot | `system_state = UNINITIALIZED`，所有 Core 字段为 None | `["uninitialized"]` |
| **输入完整性失败** | 结构性坏记录（如 .day 记录长度 != 32 字节） | `usage = rejected`，整只标的拒绝 | `["input_integrity_failure"]` |
| **peer_sample 不足** | 同方向已终止 Wave 不足 30 个 | 所有 rank 字段为 None | `["peer_sample_insufficient"]` |
| **同向对照不存在** | W-1, W-2, W-3 中没有与 W0 同方向的波 | P2 所有 momentum 和 label 为 None | `["same_dir_peers_absent"]` |
| **反向对照不存在** | W-1, W-2, W-3 中没有与 W0 反方向的波 | P3 所有 momentum 和 label 为 None | `["cross_dir_peers_absent"]` |
| **W-1 不存在** | 只有 W0（首次波），无历史波 | P4 所有 momentum 为 None | `["no_prior_wave"]` |
| **Range 未结束** | 当前在 transition 中，Range 尚未 resolution | `range_type = None`，Range 的 resolution_* 字段为 None | `["range_alive"]` |
| **数据过期** | 最后 bar 的日期距离当前日期超过阈值 | `usage = research_only`，`freshness = stale_research_only` | `["data_stale"]` |

### 退化层次

```
Level 0: 全功能 — 所有字段可用，usage = verification_only
Level 1: 概率层退化 — rank 全 None，P2-P4 全 None，Core + Range 仍可用
Level 2: Range 层退化 — Range 未结束，Range 字段部分 None，Core 仍可用
Level 3: Core 退化 — UNINITIALIZED，仅有 bar 基础信息
Level 4: 拒绝 — usage = rejected，不可消费
```

### 诚实原则

- 退化不 fallback：None 就是 None，不补零、不估计、不降级替代
- 退化可审计：每个 None 字段都有对应的 reason_code
- 退化可恢复：当条件满足时（如 peer_sample 累积到 30），自动恢复

---

## §9 测试覆盖要求

### 核心不变量测试（必须覆盖）

| 测试类别 | 最少测试数 | 覆盖内容 |
|---------|----------|---------|
| 快照字段完整性 | 2 | 全字段存在、rule_versions 完整 |
| usage 判定 | 4 | rejected、research_only、verification_only、operational（禁用） |
| reason_codes | 3 | 字段为 None 时附带 reason_code、多字段 None 时多 reason_code |
| 中断恢复 | 2 | 从 current.json 恢复、中断后增量计算 |

### 边界情况测试（必须覆盖）

| 测试类别 | 最少测试数 |
|---------|----------|
| 空快照 | 1 |
| 全字段 None | 1 |