# MALF-Core Operational Boundary Rules v1.4

> 本文件是 `MALF_Three_Part_Design_Set_v1_4` 的 Core 操作边界补丁。
> v1.4 不推翻 v1.3 的 Core 主定义、主定理和主边界；v1.4 只补足工程实现必须冻结的事件顺序、版本、比较、candidate、初始化、snapshot 与 replay 规则。
> 本文件是权威定义升级，不是 runtime proof，也不声明当前 Python、DuckDB 或 runner 已完成 v1.4 实现同步。

---

## 1. 定位

v1.3 已经完成 Core 的语义闭环：

```text
PriceBar
-> Confirmed H/L
-> HH / HL / LL / LH
-> Active Wave
-> Current Effective Guard
-> Break
-> Transition Boundary
-> Active Candidate Guard
-> Progress Confirmation
-> New Wave
```

v1.4 补的是实现闭环。任何后续 MALF-Core 实现、schema、runner、audit 或 formal proof，都必须同时满足 v1.3 语义规则与本文件的操作边界规则。

---

## 2. Rule O1：Pivot Detection Rule Version

Pivot 确认规则属于 Core 输入契约的一部分。

```text
pivot_detection_rule_version must be recorded.
same source_run_id must not mix pivot_detection_rule_version values.
same symbol + timeframe + bar_dt + pivot_type must be explainable by source_run_id + core_rule_version + pivot_detection_rule_version.
```

原因：

不同 pivot 确认规则会改变 H/L 序列，进而改变 HH/HL/LL/LH、wave、break、transition 和 candidate。如果不记录 pivot 规则版本，重放时无法判断差异来自行情输入、Core 规则，还是 pivot 检测规则。

最低实现要求：

| 对象 | 要求 |
|---|---|
| Core request | 必须携带 `pivot_detection_rule_version` |
| Core run ledger | 必须记录 `pivot_detection_rule_version` |
| pivot ledger | 必须可追溯到 `pivot_detection_rule_version` |
| replay audit | 必须校验同一 `source_run_id` 下 pivot rule 不混用 |

---

## 3. Rule O2：Core Event Ordering

同一 `symbol + timeframe + bar_dt` 内，Core 事件顺序固定如下：

```text
1. ingest PriceBar
2. confirm pivots
3. update active wave progress / current effective guard
4. evaluate break
5. if break, terminate old wave and open transition
6. update active candidate guard
7. evaluate progress confirmation
8. create new wave if confirmed
9. publish core state snapshot
```

本顺序用于解决同一 bar 内同时触发多个条件时的歧义。

规则：

| 场景 | 裁决 |
|---|---|
| 同一 bar 同时击穿 guard 和越过 transition boundary | 先按 active wave 规则 evaluate break；transition 打开后，candidate 与 confirmation 必须按本顺序重新判断 |
| break、candidate、confirmation 因 pivot 延迟确认落在同一 bar | 必须按事件顺序判定，不得把未出现的 active candidate 反推到 confirmation 前 |
| candidate 与 progress confirmation 同一 pivot | 不成立；confirmation 必须 after active candidate guard |
| 同一 bar 多个 H/L pivot | 使用 `pivot_seq_in_bar` 和 event ordering 排序 |

最低实现要求：

```text
core_event_ordering_version = core-event-order-v1
```

该版本必须进入 Core run ledger 或等价运行 manifest。

---

## 4. Rule O3：Strict Compare and Equality Policy

Core 采用严格突破。

```text
break(up wave)       = bar_low  < current_effective_HL.price
break(down wave)     = bar_high > current_effective_LH.price
up confirmation      = H > transition_boundary_high
down confirmation    = L < transition_boundary_low
```

等于不构成 break，也不构成 progress confirmation。

```text
bar_low  == guard_price              => no up-wave break
bar_high == guard_price              => no down-wave break
H        == transition_boundary_high => no up confirmation
L        == transition_boundary_low  => no down confirmation
```

最低实现要求：

| 字段 | 裁决 |
|---|---|
| `price_compare_policy` | `strict` |
| `epsilon_policy` | `none_after_price_normalization` |
| price type | 实现层必须先按 Data Foundation 正式价格精度归一化，再进入 Core compare |

禁止：

```text
Do not silently use >= or <= for break / confirmation.
Do not use runtime-dependent floating tolerance without recording policy.
```

---

## 5. Rule O4：Candidate Refresh and Replacement

Transition 中 active candidate 的定义统一为：

```text
active_candidate_guard = latest candidate_guard
```

不分同方向或相反方向，只要新的 candidate guard 出现，它就是新的 active candidate。

| 场景 | 裁决 | 事件类型 |
|---|---|---|
| candidate L1 后出现 candidate L2 | L2 替换 L1 | `same_direction_candidate_refresh` |
| candidate H1 后出现 candidate H2 | H2 替换 H1 | `same_direction_candidate_refresh` |
| candidate L 后出现 candidate H | H 替换 L，L 作废 | `opposite_direction_candidate_replacement` |
| candidate H 后出现 candidate L | L 替换 H，H 作废 | `opposite_direction_candidate_replacement` |

计数规则：

```text
candidate_replacement_count = count(candidate guard replacement events inside transition before confirmation)
```

其中同向 refresh 与反向 replacement 都属于 replacement event。若后续需要区分方向摇摆，可新增：

```text
opposite_direction_candidate_replacement_count
same_direction_candidate_refresh_count
```

在新增字段前，`candidate_replacement_count` 不得只解释为相反方向替换次数。

---

## 6. Rule O5：Transition Primitive Context

Transition 内的 pivot 仍允许形成结构原语，但其上下文必须与 active wave 分离。

采用方案 A：

```text
transition pivots may enter malf_structure_ledger.
their structure_context must be transition_candidate.
transition_candidate primitives must not update old wave progress.
transition_candidate primitives must not update old wave current effective guard.
transition_candidate primitives only serve candidate / confirmation audit.
```

含义：

| 上下文 | 可做什么 | 不可做什么 |
|---|---|---|
| `active_wave` | 更新 active wave progress / guard | 跨 transition 使用 |
| `transition_candidate` | 留痕 candidate 与 confirmation 过程 | 更新 old wave 或创建 confirmed wave |
| `initial_candidate` | 留痕初始候选结构 | 触发 break 或 transition |

这样 `malf_structure_ledger` 不断层，同时不会把 transition 误当成 wave。

---

## 7. Rule O6：Initial Candidate Reset

初始化阶段只能创建 initial candidate，不能产生 break 或 transition。

初始 wave 成立条件保持 v1.3：

```text
initial up wave   = H0 -> L1 -> H2 and H2 > H0
initial down wave = L0 -> H1 -> L2 and L2 < L0
```

失败规则：

| 场景 | 裁决 |
|---|---|
| `H0 -> L1 -> H2` 且 `H2 <= H0` | 不创建 wave，不 break，不 transition |
| `L0 -> H1 -> L2` 且 `L2 >= L0` | 不创建 wave，不 break，不 transition |
| 初始化阶段出现更高 H | 可替换 initial up reference H0 |
| 初始化阶段出现更低 L | 可替换 initial down reference L0 |
| 初始化阶段结构不足 | `system_state = uninitialized`; `structure_context = initial_candidate` |

最低审计要求：

```text
No initial candidate failure may create a terminated wave.
No initial candidate failure may open a transition.
No initial candidate failure may be counted as break.
```

---

## 8. Rule O7：Core State Snapshot Contract

Core event ledger 负责追溯，Core snapshot 负责读取。

后续实现同步时应新增或等价提供：

```text
malf_core_state_snapshot
```

最小字段：

| 字段 | 说明 |
|---|---|
| `symbol` | 标的 |
| `timeframe` | 时间级别 |
| `bar_dt` | snapshot 所属 bar |
| `system_state` | `uninitialized / up_alive / down_alive / transition` |
| `active_wave_id` | alive 状态下的 active wave |
| `old_wave_id` | transition 状态下的 old wave |
| `direction` | alive 方向；transition 中为 old_direction |
| `wave_core_state` | `alive / terminated`，不得为 transition |
| `current_effective_guard_pivot_id` | 当前有效守护 pivot |
| `current_effective_guard_price` | 当前有效守护价格 |
| `progress_extreme_pivot_id` | 当前推进极值 pivot |
| `progress_extreme_price` | 当前推进极值价格 |
| `open_transition_id` | 当前 open transition |
| `active_candidate_guard_pivot_id` | 当前 active candidate guard |
| `active_candidate_direction` | 当前 candidate direction |
| `core_rule_version` | Core 规则版本 |
| `pivot_detection_rule_version` | Pivot 检测规则版本 |
| `core_event_ordering_version` | Core 事件顺序版本 |
| `price_compare_policy` | 价格比较策略 |
| `source_run_id` | 输入来源 run |
| `run_id` | 本次 Core run |

snapshot 必须能由 Core ledger 重放校验；Service 不应每次从全量事件账本临时推导 latest state。

---

## 9. Rule O8：Replay Determinism

相同输入和规则必须可重放。

```text
same source facts
+ same source_run_id
+ same core_rule_version
+ same pivot_detection_rule_version
+ same core_event_ordering_version
+ same price_compare_policy
=> same pivots, structures, waves, breaks, transitions, candidates, snapshots
```

重放差异必须能归因到以下至少一项：

| 差异来源 | 必须记录 |
|---|---|
| source facts changed | source manifest / source_run_id |
| pivot rule changed | `pivot_detection_rule_version` |
| Core semantic rule changed | `core_rule_version` |
| event ordering changed | `core_event_ordering_version` |
| price compare changed | `price_compare_policy` |
| schema changed | `schema_version` |

禁止把 replay 差异解释为“正常浮动”而不落版本或 manifest。

---

## 10. v1.4 不授权事项

本文件不授权：

```text
Python implementation sync
DuckDB schema migration
formal DB rebuild
week/month proof
MALF full build
Alpha full build
Signal full build
Position construction
downstream construction
full-chain pipeline runtime
```

任何实现同步必须另开执行卡，并在 repo 执行四件套、report closeout、validated evidence 与 governance registry 中落档。

---

## 11. 一句话结论

```text
MALF v1.4 = MALF v1.3 semantic authority + Core operational boundary rules.
```

人话版：

```text
v1.3 把 Core 的“意思”讲清楚了；v1.4 把实现时必须怎么排队、怎么比较、怎么记账、怎么重放钉住。
```
