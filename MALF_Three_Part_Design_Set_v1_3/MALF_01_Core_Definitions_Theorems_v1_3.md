# MALF-Core 定义与定理：语义定稿 v1.3

> 本文件是 `MALF_Three_Part_Design_Set_v1_3` 的 Core 权威定义。  
> 本版重点修正 Break、Transition Reference、Candidate Guard、New Wave confirmation 的歧义。  
> 本文件只定义 Core 语义，不声明当前实现已覆盖全部新增字段。

---

## 0. 总述

### 0.0 先读这几句话

Core（结构层）的任务很朴素：从价格 K 线里找出确认高低点，再判断一条波段生命是否出生、是否还活着、何时死亡、死亡后怎样确认下一条新波段。

本文件里几个词可以先这样理解：

| 术语 | 中文落点 | 人话解释 |
|---|---|---|
| `PriceBar` | 价格 bar / K 线 | 原始价格输入 |
| `Pivot` | 确认极值 | 已确认的 H 或 L |
| `Primitive` | 结构原语 | HH / HL / LL / LH |
| `Wave` | 波段生命 | 有方向、有推进、有守护、有终止的结构 |
| `Current Effective Guard` | 当前有效守护点 | 当前这条活波段真正用来判死活的 HL 或 LH |
| `Break` | 击穿 / 破守护 | 当前有效守护点被打穿，旧波死亡 |
| `Transition` | 转换未决区 | 旧波死了，新波还没确认 |
| `Transition Boundary` | 转换边界 | 旧波死亡后留下的上下边界 |
| `Candidate Guard` | 候选守护点 | 新波出生前先出现的候选 L 或 H |
| `Progress Confirmation` | 推进确认 | 候选之后真正突破边界，确认新波出生 |

一句话主线：

```text
价格 -> H/L -> HH/HL/LL/LH -> 活波段 -> 守护被击穿 -> transition -> 候选守护 -> 推进确认 -> 新波段
```

### 0.1 MALF-Core 的定义

**MALF-Core 是一个以价格序列为输入，以确认极值为最小结构单位，以 HH / HL / LL / LH 为结构原语，以上涨结构、下跌结构、转换区为核心系统状态，以当前有效守护原语被击穿触发旧 wave 终止，以 transition boundary、active candidate guard 与后续 progress confirmation 共同触发 new wave 创建的结构语义系统。**

压缩表达：

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

### 0.2 本文件回答什么

| 问题 | 是否回答 |
|---|---:|
| 什么是 H / L | 是 |
| 什么是 HH / HL / LL / LH | 是 |
| 什么是 current effective guard | 是 |
| 什么是 wave | 是 |
| 哪一个 HL / LH 会触发 break | 是 |
| break 后旧 wave 是否继续 | 是：不继续 |
| break 后 transition 保存什么 | 是 |
| new wave 从什么时候确认 | 是 |
| new wave 的强弱或统计位置 | 否，交给 Lifespan |
| 是否买卖或建仓 | 否，MALF 不输出交易动作 |

---

## 1. 基础对象

### 定义 D1：PriceBar

PriceBar 是 MALF-Core 的输入价格记录。

```text
PriceBar = symbol + timeframe + bar_dt + open + high + low + close
```

MALF-Core 不直接从抽象情绪、信号或下游判断生成结构。所有 Core 结构必须最终追溯到 PriceBar。

### 定义 D2：确认极值

确认极值是从价格序列中确认出的局部高点或局部低点。

```text
Pivot ∈ {H, L}
```

| 极值 | 定义 |
|---|---|
| H | confirmed high pivot |
| L | confirmed low pivot |

确认规则可由实现层指定。进入 Core 后，极值只表现为 H 或 L。

### 定义 D3：结构上下文

结构上下文决定当前 H / L 与哪个 reference H / L 比较。

```text
StructureContext ∈ {
    active_wave,
    transition_candidate,
    initial_candidate
}
```

| 上下文 | reference 来源 |
|---|---|
| active_wave | 当前 active wave 内最新相关同类极值 |
| transition_candidate | transition boundary 与 active candidate guard |
| initial_candidate | 初始化阶段候选 wave 的 reference pivot |

“相关”不是任意历史极值，必须由当前结构上下文指定。

### 定义 D4：结构原语

结构原语由当前确认极值与结构上下文中的 reference H / L 比较得到。

```text
Primitive ∈ {HH, HL, LL, LH}
```

| 原语 | 完整名 | 定义 |
|---|---|---|
| HH | Higher High | 当前 H 高于当前结构上下文的 reference H |
| HL | Higher Low | 当前 L 高于当前结构上下文的 reference L |
| LL | Lower Low | 当前 L 低于当前结构上下文的 reference L |
| LH | Lower High | 当前 H 低于当前结构上下文的 reference H |

### 定义 D5：结构方向

MALF-Core 只承认两种方向性结构：

```text
StructureDirection ∈ {up, down}
```

| 方向 | 推进原语 | 守护原语 |
|---|---|---|
| up | HH | HL |
| down | LL | LH |

---

## 2. Wave 与当前有效守护

### 定义 D6：上涨结构

上涨结构是以 HH 为推进原语、以 HL 为守护原语的方向性结构。

```text
UpStructure =
    direction = up
    progress_primitive = HH
    guard_primitive = HL
```

### 定义 D7：下跌结构

下跌结构是以 LL 为推进原语、以 LH 为守护原语的方向性结构。

```text
DownStructure =
    direction = down
    progress_primitive = LL
    guard_primitive = LH
```

### 定义 D8：Wave

Wave 是一个有方向、有开始、有推进原语、有当前有效守护原语、有终止条件的结构对象。

```text
Wave =
    wave_id
    direction
    wave_core_state
    start_dt
    progress_extreme
    current_effective_guard
    terminated_dt?
```

```text
wave_core_state ∈ {alive, terminated}
```

### 定义 D9：Current Effective Guard

Current Effective Guard 是 active wave 当前仍有效的守护原语。

```text
current_effective_HL(up wave) =
    latest confirmed HL inside the active up wave

current_effective_LH(down wave) =
    latest confirmed LH inside the active down wave
```

| Active wave | Current effective guard | 价格字段 |
|---|---|---|
| up wave | 最新确认且仍有效的 HL | guard L price |
| down wave | 最新确认且仍有效的 LH | guard H price |

初始 wave 的 first guard：

| Initial wave | first guard |
|---|---|
| initial up wave | `H0 -> L1 -> H2 > H0` 中的 L1 |
| initial down wave | `L0 -> H1 -> L2 < L0` 中的 H1 |

Progress update 不自动替换 guard：

```text
HH update updates progress_extreme only.
LL update updates progress_extreme only.
Only a later confirmed HL replaces current_effective_HL.
Only a later confirmed LH replaces current_effective_LH.
```

---

## 3. Break 与 System State

### 定义 D10：Break

Break 是 active wave 的当前有效守护原语被后续价格击穿所触发的结构终止事件。

```text
break(up wave) =
    bar_low < current_effective_HL.price

break(down wave) =
    bar_high > current_effective_LH.price
```

这里的 HL / LH 必须是当前 active wave 内的 current effective guard，不得解释为：

```text
not any historical HL / LH
not the first HL / LH unless it is still current effective guard
not the break bar high / low
not a downstream interpretation
```

Break 必须记录：

| 字段 | 含义 |
|---|---|
| old_wave_id | 被终止的 active wave |
| old_direction | 旧 wave 方向 |
| broken_guard_primitive | 被击穿的守护原语：HL 或 LH |
| broken_guard_pivot_id | 被击穿的守护 pivot |
| broken_guard_price | 被击穿的守护价格 |
| old_final_progress_extreme_pivot_id | 旧 wave 最终推进极值 pivot |
| old_final_progress_extreme_price | 旧 wave 最终推进极值价格 |
| break_dt | break 日期 |

Break 发生后：

```text
old_wave.wave_core_state = terminated
system_state = transition
```

### 定义 D11：System State

System State 描述当前 MALF-Core 系统处于哪个阶段。

```text
system_state ∈ {
    uninitialized,
    up_alive,
    down_alive,
    transition
}
```

| system_state | 定义 |
|---|---|
| uninitialized | 尚未确认第一个 wave |
| up_alive | 当前有 active up wave |
| down_alive | 当前有 active down wave |
| transition | 旧 wave 已 terminated，新 wave 尚未 confirmed |

`system_state` 与 `wave_core_state` 不得混用。

---

## 4. Transition 双边界模型

### 定义 D12：Transition

Transition 是 old wave terminated 之后、new wave confirmed 之前的 system_state。

```text
Transition =
    after old_wave.terminated
    before new_wave.confirmed
```

Transition 不属于旧 wave，不表示旧 wave 复活，只表示结构未决。

Transition 必须保存：

| 字段 | 含义 |
|---|---|
| transition_id | transition 编号 |
| old_wave_id | 被终止的旧 wave |
| old_direction | 旧 wave 方向，必填 |
| break_dt | 进入 transition 的日期 |
| broken_guard_pivot_id | 被击穿的当前有效 guard |
| broken_guard_price | 被击穿的当前有效 guard 价格 |
| old_final_progress_extreme_pivot_id | 旧 wave 最终推进极值 pivot |
| old_final_progress_extreme_price | 旧 wave 最终推进极值价格 |
| transition_boundary_high | transition 上边界 |
| transition_boundary_low | transition 下边界 |
| state | open / confirmed |

### 定义 D13：Transition Boundary

Transition Boundary 是 break 后由 transition 接管的新生命确认边界。

```text
old up wave break:
    transition_boundary_high = old final HH price
    transition_boundary_low  = broken current_effective_HL price

old down wave break:
    transition_boundary_high = broken current_effective_LH price
    transition_boundary_low  = old final LL price
```

解释：

```text
old wave does not participate in the new life.
transition owns the boundary.
```

不得使用：

```text
not break bar high / low
not temporary high / low inside transition unless it becomes active candidate guard
not arbitrary historical H / L
not a single old_progress_extreme for both directions
```

---

## 5. Candidate 与 New Wave

### 定义 D14：Candidate Guard

Candidate Guard 是用于确认 new wave 的候选守护极值。

| 候选方向 | candidate_guard |
|---|---|
| candidate up wave | transition 或 initialization 中确认的 L |
| candidate down wave | transition 或 initialization 中确认的 H |

Candidate Guard 先于 progress confirmation 出现。

```text
no candidate_guard => no new_wave_confirmed
```

### 定义 D15：Candidate Direction

Candidate Direction 是由最新 candidate_guard 决定的候选方向。

| 最新 candidate_guard | candidate_direction |
|---|---|
| latest L | up |
| latest H | down |

在 transition 中，同一时刻只允许存在一个 active candidate。

```text
active_candidate = latest_candidate_guard
```

旧 candidate 一旦被更新的相反方向 candidate_guard 替代，即作废。

### 定义 D16：Progress Confirmation

Progress Confirmation 是 active candidate_guard 之后出现的方向性推进确认。

| Active candidate | Progress confirmation |
|---|---|
| candidate up wave | active candidate L 之后，出现 H 且 H > transition_boundary_high |
| candidate down wave | active candidate H 之后，出现 L 且 L < transition_boundary_low |

Progress confirmation 必须发生在 active candidate guard 之后。

### 定义 D17：New Wave

New Wave 是 transition 之后，经 active candidate guard 与后续 progress confirmation 共同确认的新方向性结构。

```text
new_wave_confirmed =
    active_candidate_guard exists
    and progress_confirmation occurs after active_candidate_guard
```

| New Wave 来源 | 定义 |
|---|---|
| same-direction new wave | break 后确认与旧 wave 同方向的新 wave |
| opposite-direction new wave | break 后确认与旧 wave 反方向的新 wave |

不得使用“candidate 方向 + confirmed”这类旧式缩写作为正式术语。

正式表达必须是：

```text
new up wave confirmed by active candidate L + later H > transition_boundary_high
new down wave confirmed by active candidate H + later L < transition_boundary_low
```

### 定义 D18：Initial Wave

Initial Wave 是 `system_state = uninitialized` 时确认出的第一个 wave。

| 初始方向 | 确认序列 |
|---|---|
| initial up wave | `H0 -> L1 -> H2`，且 `H2 > H0`；L1 为 first candidate_guard |
| initial down wave | `L0 -> H1 -> L2`，且 `L2 < L0`；H1 为 first candidate_guard |

结构不足时：

```text
system_state = uninitialized
state = initial_candidate
```

---

## 6. 定理

### 定理 T1：结构原语上下文定理

HH / HL / LL / LH 必须由当前结构上下文指定 reference 后才能成立。

```text
primitive = compare(current_pivot, reference_pivot_in_context)
```

### 定理 T2：方向配对定理

上涨结构必须同时具有 HH 推进语义与 HL 守护语义；下跌结构必须同时具有 LL 推进语义与 LH 守护语义。

```text
up = HH progress + HL guard
down = LL progress + LH guard
```

### 定理 T3：当前有效守护唯一性定理

一个 active wave 在任一时刻只有一个 current effective guard。

```text
active_up_wave.current_effective_guard = latest valid HL
active_down_wave.current_effective_guard = latest valid LH
```

### 定理 T4：旧波不可复活定理

Wave 一旦 terminated，就不能重新变回 alive。

```text
terminated(wave) => never alive again
```

后续只能创建 new wave。

### 定理 T5：Candidate 最新有效定理

Transition 中同一时刻只允许一个 active candidate。Active candidate 必须由最新 candidate_guard 决定。

```text
active_candidate = latest(candidate_guard)
```

如果新出现的 candidate_guard 与当前 active candidate 方向相反：

```text
old_candidate = invalidated
new_candidate = active
```

| 场景 | 结果 |
|---|---|
| candidate L 出现 | active candidate = up |
| 后续 candidate H 出现 | old up candidate 作废，active candidate = down |
| 后续又 candidate L 出现 | old down candidate 作废，active candidate = up |

### 定理 T6：新波双条件确认定理

New wave 的确认必须同时满足：

```text
active_candidate_guard exists
progress_confirmation occurs after active_candidate_guard
```

| 条件 | 是否可确认 new wave |
|---|---:|
| 只有 candidate_guard | 否 |
| 只有突破 transition boundary，但无 active candidate_guard | 否 |
| active candidate_guard + 后续 progress confirmation | 是 |

### 定理 T7：Break 后新波创建定理

Break 之后出现的任何已确认新结构，都必须创建 new wave，不得延伸 old wave。

| 旧 wave | break 事件 | 后续确认 | 结果 |
|---|---|---|---|
| Up Wave | current_effective_HL broken | active candidate L + H > transition_boundary_high | New Up Wave |
| Up Wave | current_effective_HL broken | active candidate H + L < transition_boundary_low | New Down Wave |
| Down Wave | current_effective_LH broken | active candidate H + L < transition_boundary_low | New Down Wave |
| Down Wave | current_effective_LH broken | active candidate L + H > transition_boundary_high | New Up Wave |

### 定理 T8：Transition 非波段定理

Transition 不是 wave。

```text
transition != wave
```

Transition 只负责连接：

```text
old wave terminated -> transition boundary -> new wave confirmed
```

### 定理 T9：旧波边界遗产定理

Old wave terminated 后不参与新生命，但 break 时留下 transition boundary。

```text
old_wave after break = audit history only
transition_boundary = inherited structural boundary
```

### 定理 T10：交易非输出定理

MALF-Core 不输出交易动作。

```text
Core output != buy
Core output != sell
Core output != weight
Core output != order
```

---

## 7. 数据对象

| Core ledger | 职责 |
|---|---|
| `malf_pivot_ledger` | 存 H / L |
| `malf_structure_ledger` | 存 HH / HL / LL / LH |
| `malf_wave_ledger` | 存 wave 的创建、方向、终止 |
| `malf_break_ledger` | 存 break 事件与 broken guard |
| `malf_transition_ledger` | 存 transition 与 transition boundary |
| `malf_candidate_ledger` | 存 candidate_guard、active candidate、confirmation |

v1.3 设计字段不等于当前实现已全部落地。实现同步需要另开卡。

---

## 8. 最终句

### 标准版

**MALF-Core 从价格序列中识别确认极值，将极值组织为 HH / HL / LL / LH 结构原语，再由结构原语形成上涨结构或下跌结构；当 active wave 的当前有效守护原语被 break 时，旧 wave 立即 terminated，system_state 进入 transition；transition 接管 high / low 双边界，最新 active candidate guard 与后续 progress confirmation 共同确认 new wave。**

### 铁律版

```text
Break kills the old wave.
Transition owns the boundary.
Candidate is not wave.
New wave requires guard plus later confirmation.
```
