# MALF 三件套桥接说明 v1.4

> 本文件是 `MALF_Three_Part_Design_Set_v1_4` 的入口文件。
> v1.4 是 MALF Core 操作边界权威升级包，不是实现闭环报告，不改变当前 Asteria runtime gate。
> v1.4 保留 v1.3 的 Core / Lifespan / Service 语义主线，并新增 `MALF_01B_Core_Operational_Boundary_Rules_v1_4.md`，把 Core 工程边界补成可施工、可测试、可审计、可重放的规则。

---

## 0. 阅读提示

本包分成三层读法：

| 读法 | 适合谁 | 怎么读 |
|---|---|---|
| 权威语义版 | 实现、审计、后续同步 | 先读 Core / Lifespan / Service 定义 |
| 操作边界版 | Core 实现、schema、runner、audit | 重点读 `MALF_01B_Core_Operational_Boundary_Rules_v1_4.md` |
| 图表理解版 | 快速理解、复盘、讨论 | 先看流程图和表，再回到权威定义 |

几个常用英文术语在本包中的中文落点：

| 英文术语 | 中文理解 |
|---|---|
| `Core` | 结构层，回答波段是否成立 |
| `Lifespan` | 生命统计层，回答波段现在处在什么位置 |
| `Service` | 只读服务层，把结构和位置发布给 Alpha |
| `Wave` | 波段生命 |
| `Break` | 守护点被击穿，旧波段死亡 |
| `Transition` | 旧波死亡后、新波确认前的未决区 |
| `Candidate Guard` | 候选守护极值，新波出生前的守护点 |
| `Progress Confirmation` | 推进确认，新波真正成立的确认动作 |
| `WavePosition` | 波段位置坐标，给 Alpha 读取 |

一句人话版：

```text
v1.3 讲清楚 Core 是什么意思；v1.4 补清楚 Core 工程上怎么排队、怎么比较、怎么记账、怎么重放。
```

## 1. 本版目标

v1.4 不推翻 v1.3。v1.3 解决了三个主要语义问题：

1. `break(up wave) = break(HL)` 必须指当前 active wave 内的 `current_effective_HL`。
2. `candidate guard` 与 `progress confirmation` 必须分开，不再使用 `candidate confirmed` 混词。
3. `transition_boundary_high / transition_boundary_low` 同时覆盖 same-direction 与 opposite-direction new wave。

v1.4 在此基础上补足八个操作边界：

1. `pivot_detection_rule_version`
2. same-bar / Core event ordering
3. strict compare / equality policy
4. candidate refresh / replacement rule
5. transition primitive context
6. initial candidate reset rule
7. `malf_core_state_snapshot` contract
8. replay determinism rule

## 2. Core 主轴

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
-> Core State Snapshot
```

最后的 `Core State Snapshot` 是 v1.4 操作边界补丁新增的读取/审计落点；它不改变 v1.3 语义主轴，只补工程闭环。

---

## 3. 本包文件

| 文档 | 职责 |
|---|---|
| `MALF_00_Three_Documents_Bridge_v1_4.md` | v1.4 入口、版本关系、治理边界 |
| `MALF_01_Core_Definitions_Theorems_v1_4.md` | 继承 v1.3 Core 主定义与主定理；文件名升级为 v1.4 baseline |
| `MALF_01B_Core_Operational_Boundary_Rules_v1_4.md` | v1.4 新增 Core 操作边界规则 |
| `MALF_02_Lifespan_Stats_Definitions_Theorems_v1_4.md` | 继承 v1.3 Lifespan 统计定义与 birth descriptors |
| `MALF_03_System_Service_Interface_v1_4.md` | 继承 v1.3 Service 只读接口与 transition trace |
| `MALF_04_Core_Chart_View_v1_4.md` | Core 图表版，辅助理解结构生成、break、transition 与 new wave |
| `MALF_05_Lifespan_Chart_View_v1_4.md` | Lifespan 图表版，辅助理解生命统计、rank 与出生描述 |
| `MALF_06_Service_Chart_View_v1_4.md` | Service 图表版，辅助理解只读接口与字段分组 |
| `MALF_07_Definition_Theorem_Review_and_Implementation_Delta_v1_4.md` | 继承 v1.3 定义/定理评审结论，并由 01B 补充后续实现差异 |

说明：

```text
v1.4 baseline files inherit v1.3 semantic content.
01B is the normative v1.4 delta.
```

---

## 4. 三层关系

```text
Core determines whether a wave exists.
Lifespan describes where the wave stands.
Service publishes the read-only position surface.
```

v1.4 对三层关系的补充是：

```text
Core operational rules determine whether implementation can be replayed and audited.
```

### 4.1 Core

Core 只回答结构事实：

```text
Which pivots are confirmed?
Which structure primitives exist?
Which wave is alive?
Which guard kills it?
Which transition is open?
Which candidate guard is active?
Which confirmation creates the new wave?
Which snapshot represents current Core state?
```

Core 不回答价值、不回答买卖、不回答仓位、不回答订单。

### 4.2 Lifespan

Lifespan 只统计 confirmed wave：

```text
new_count
no_new_span
transition_span
rank
life_state
birth descriptors
```

Lifespan 不修改 Core，不创建 wave。

### 4.3 Service

Service 只读发布：

```text
WavePosition = Core trace + Lifespan stats
```

Service 不解释机会、不输出交易动作、不允许下游写回。

---

## 5. v1.4 治理边界

v1.4 当前地位：

| 项 | 裁决 |
|---|---|
| 语义权威 | 是，作为当前 MALF Core 操作边界权威 |
| runtime proof | 否 |
| formal DB rebuild | 否 |
| week/month proof | 否 |
| downstream authorization | 否 |

当前 Asteria runtime evidence 仍以：

```text
malf-v1-3-formal-rebuild-closeout-20260502-01
```

为 MALF day formal-data bounded proof。v1.4 是后续实现同步和 formal proof 的权威输入，不得被表述为已经通过 v1.4 runtime proof。

---

## 6. 后续实现同步必须覆盖

| 边界 | 后续实现同步要求 |
|---|---|
| pivot rule version | request、run ledger、pivot ledger、replay audit 必须记录 |
| event ordering | 同一 bar 内必须按 `core-event-order-v1` 执行 |
| strict compare | 等于不触发 break/confirmation |
| candidate refresh | active candidate 永远等于 latest candidate guard |
| transition primitive context | transition 内 primitive 使用 `transition_candidate` |
| initial reset | 初始确认失败不创建 wave / break / transition |
| snapshot contract | 提供 `malf_core_state_snapshot` 或等价快照 |
| replay determinism | 同输入同版本必须重放一致 |

---

## 7. 一句话结论

```text
MALF v1.4 = MALF v1.3 semantic authority + Core operational boundary rules.
```

人话版：

```text
Core 的主线不用推倒，v1.4 只是把实现一定会撞到的边界钉死。
```
