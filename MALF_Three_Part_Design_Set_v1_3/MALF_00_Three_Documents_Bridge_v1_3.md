# MALF 三件套桥接说明 v1.3

> 本文件是 `MALF_Three_Part_Design_Set_v1_3` 的入口文件。  
> v1.3 是 MALF 权威定义升级包，不是实现闭环报告，不改变当前 Asteria gate。  
> 本包只定义 MALF 语义、统计与服务边界；代码实现、本地 repo docs 同步、治理 registry 更新需要另开卡。

---

## 0. 阅读提示

本包分成两层读法：

| 读法 | 适合谁 | 怎么读 |
|---|---|---|
| 权威定义版 | 实现、审计、后续同步 | 逐条看定义、字段、定理 |
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
Core 负责判生死，Lifespan 负责看年龄和位置，Service 负责把结果只读发布出去。
```

## 1. 本版目标

v1.3 解决 v1.2 / Core v1.3 中三个容易误解的权威定义问题：

1. `break(up wave) = break(HL)` 没有明确是哪一个 HL。
2. “candidate 方向 + confirmed” 这类旧式缩写混淆了 candidate 与 new wave confirmation。
3. `old_progress_extreme_price` 单点 reference 无法严谨覆盖 same-direction 与 opposite-direction new wave。

本版将 MALF-Core 主轴重写为：

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

---

## 2. 三份核心文档

| 文档 | 职责 |
|---|---|
| `MALF_01_Core_Definitions_Theorems_v1_3.md` | 定义 PriceBar 到 wave / break / transition / new wave 的结构语义 |
| `MALF_02_Lifespan_Stats_Definitions_Theorems_v1_3.md` | 定义 confirmed wave 的生命统计、rank、birth descriptors 与 WavePosition |
| `MALF_03_System_Service_Interface_v1_3.md` | 定义 MALF 对 Alpha 的只读服务接口、字段边界、禁止输出 |
| `MALF_04_Core_Chart_View_v1_3.md` | Core 图表版，辅助理解结构生成、break、transition 与 new wave |
| `MALF_05_Lifespan_Chart_View_v1_3.md` | Lifespan 图表版，辅助理解生命统计、rank 与出生描述 |
| `MALF_06_Service_Chart_View_v1_3.md` | Service 图表版，辅助理解只读接口与字段分组 |
| `MALF_07_Definition_Theorem_Review_and_Implementation_Delta_v1_3.md` | v1.3 定义/定理评审结论与后续实现差异表 |

三件套关系：

```text
Core determines whether a wave exists.
Lifespan describes where the wave stands.
Service publishes the read-only position surface.
```

---

## 3. v1.3 的关键裁决

### 3.1 Break 的 guard 是当前有效 guard

`HL` / `LH` 不是任意历史原语。

```text
current_effective_HL = active up wave 内最新确认且仍有效的 HL
current_effective_LH = active down wave 内最新确认且仍有效的 LH
```

因此：

```text
break(up wave)   = price breaks current_effective_HL
break(down wave) = price breaks current_effective_LH
```

### 3.2 Break 后旧 wave 死亡

旧 wave 一旦 terminated：

```text
terminated(wave) => never alive again
```

旧 wave 不参与新生命。它只留下审计事实与 transition boundary。

### 3.3 Transition 使用双边界模型

Transition 不再使用单一 `old_progress_extreme_price` 作为全部候选方向的 reference。

```text
old up wave break:
    transition_boundary_high = old final HH
    transition_boundary_low  = broken current_effective_HL

old down wave break:
    transition_boundary_high = broken current_effective_LH
    transition_boundary_low  = old final LL
```

### 3.4 New wave 只能由双条件确认

不得再使用未定义的 `candidate confirmed` 说法。

```text
new_wave_confirmed =
    active_candidate_guard exists
    and progress_confirmation occurs after active_candidate_guard
```

Candidate guard 只是候选守护，不是 wave。Transition 也不是 wave。

---

## 4. 主线边界

MALF 只负责结构事实与统计位置。

```text
MALF defines structure and position.
Alpha interprets value.
Signal aggregates intent.
Position materializes holding logic.
Portfolio allocates capital.
Trade executes orders.
System reads out the whole chain.
Pipeline orchestrates, but does not redefine business meaning.
```

MALF 禁止输出：

```text
buy
sell
weight
order
position_size
portfolio_allocation
```

MALF 禁止接受下游写回。

---

## 5. 与实现状态的关系

v1.3 是权威定义升级，不是当前代码实现声明。

| 项 | 本包裁决 |
|---|---|
| 是否修改 `H:\Asteria` repo | 否 |
| 是否修改本地 `docs/02-modules/malf/` | 否 |
| 是否修改 Python 实现 | 否 |
| 是否创建 DuckDB | 否 |
| 是否改变当前 gate | 否 |
| 是否声明新增字段已实现 | 否 |

后续若要同步 repo 本地设计说明或实现新增字段，必须另开同步/施工卡，并按 Asteria governance 执行验证。

`MALF_07_Definition_Theorem_Review_and_Implementation_Delta_v1_3.md` 记录本版
定义与定理的评审结论：语义层清晰、定理层自洽，可以作为后续 repo 文档同步和
代码修订卡的设计依据；但它不声明现有实现已经覆盖 v1.3 新增字段。

---

## 6. 铁律

```text
Break kills the old wave.
Transition owns the boundary.
Candidate is not wave.
New wave requires guard plus later confirmation.
Rank is position, not prediction.
MALF serves structure and position only.
```
