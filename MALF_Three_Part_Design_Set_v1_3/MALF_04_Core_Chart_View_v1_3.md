# MALF-Core 图表版辅助理解 v1.3

> 本文件是 Core 的图表阅读版。  
> 它帮助理解 `MALF_01_Core_Definitions_Theorems_v1_3.md`，但不替代权威定义。

---

## 1. 一图看 Core 主线

```mermaid
flowchart LR
    A["PriceBar<br/>价格 bar"] --> B["Confirmed H/L<br/>确认高低点"]
    B --> C["HH / HL / LL / LH<br/>结构原语"]
    C --> D{"Active Wave?<br/>是否已有活波段"}
    D -->|No| E["Initial Candidate<br/>初始候选"]
    E --> F{"Initial Confirmation?<br/>初始确认"}
    F -->|H0-L1-H2 and H2>H0| G["Up Wave Alive<br/>上涨波段存活"]
    F -->|L0-H1-L2 and L2<L0| H["Down Wave Alive<br/>下跌波段存活"]
    D -->|Up| G
    D -->|Down| H
    G --> I{"current_effective_HL broken?<br/>当前有效 HL 被击穿"}
    H --> J{"current_effective_LH broken?<br/>当前有效 LH 被突破"}
    I -->|No| G
    J -->|No| H
    I -->|Yes| K["Transition<br/>转换未决区"]
    J -->|Yes| K
    K --> L["Active Candidate Guard<br/>最新候选守护点"]
    L --> M{"Progress Confirmation?<br/>推进确认"}
    M -->|Up confirmation| G
    M -->|Down confirmation| H
    M -->|No| K
```

---

## 2. 活波段的两个核心部件

| 方向 | 推进点 | 守护点 | 人话理解 |
|---|---|---|---|
| up | HH | HL | 不断创新高，同时回落不能打穿当前有效 HL |
| down | LL | LH | 不断创新低，同时反弹不能突破当前有效 LH |

关键点：

```text
HH / LL = 生命往前走
HL / LH = 生命还守得住
```

---

## 3. 哪个 HL / LH 会触发 Break

```mermaid
flowchart TD
    A["Up Wave Alive<br/>上涨波段存活"] --> B["latest valid HL<br/>最新有效 HL"]
    B --> C{"bar_low < HL price?"}
    C -->|No| D["Up Wave Continues<br/>旧波继续存活"]
    C -->|Yes| E["Break<br/>旧 up wave 死亡"]

    F["Down Wave Alive<br/>下跌波段存活"] --> G["latest valid LH<br/>最新有效 LH"]
    G --> H{"bar_high > LH price?"}
    H -->|No| I["Down Wave Continues<br/>旧波继续存活"]
    H -->|Yes| J["Break<br/>旧 down wave 死亡"]
```

不要把 `break(HL)` 理解成任意历史 HL。它只指当前 active up wave 内最新确认且仍有效的 HL。

---

## 4. Break 后的双边界

| 旧波方向 | transition_boundary_high | transition_boundary_low |
|---|---|---|
| old up wave break | old final HH | broken current_effective_HL |
| old down wave break | broken current_effective_LH | old final LL |

人话版：

```text
旧波死了，不再参与新生命。
Transition 接管旧波死亡时留下的上下边界。
新波只突破 transition boundary，不复活旧波。
```

---

## 5. New Wave 确认

```mermaid
flowchart LR
    A["Transition<br/>转换未决"] --> B{"Latest Candidate Guard<br/>最新候选守护点"}
    B -->|L| C["Candidate Up<br/>候选上涨"]
    B -->|H| D["Candidate Down<br/>候选下跌"]
    C --> E{"Later H > transition_boundary_high?"}
    D --> F{"Later L < transition_boundary_low?"}
    E -->|Yes| G["New Up Wave Confirmed<br/>新上涨波段成立"]
    F -->|Yes| H["New Down Wave Confirmed<br/>新下跌波段成立"]
    E -->|No| A
    F -->|No| A
```

正式条件：

```text
new_wave_confirmed =
    active_candidate_guard exists
    and progress_confirmation occurs after active_candidate_guard
```

---

## 6. Core 铁律

```text
Break kills the old wave.        # Break 之后旧波死亡
Transition owns the boundary.    # Transition 接管上下边界
Candidate is not wave.           # Candidate 只是候选，不是波段
New wave requires guard + confirmation.
                                  # 新波必须有候选守护 + 后续推进确认
```

