# MALF v2.1 Core — 结构状态机

> 层：L1 — Core（结构状态机）
>
> 基于：v2.0 Core（claude-20260616）+ IMPLEMENTATION-CONTRACT-PATCH 第 1-3 层 + v1.4 操作边界 O1-O8
>
> 作者：DeepSeek
>
> 日期：2026-07-26

---

## §1 层职责

Core 层是 MALF 的唯一状态机。它从 PriceBar 序列中识别结构事实：

- **Pivot**（极值点）：分形 k=2 延迟确认
- **Primitive**（原语）：两个相邻 pivot 构成的推进段
- **Wave**（波段）：由同向 primitive 构成的持续结构
- **Guard**（守护点）：alive 期间的最近回撤 pivot
- **Break**（结构破坏）：价格突破 guard 触发 wave 终止
- **Transition**（过渡期）：break 后到 new wave 确认前的中间态
- **New Wave**（新波）：transition 内双条件满足后确认

Core 层不计算统计量、不排名、不输出概率。它只输出结构事实。

---

## §2 基础对象

### D1 PriceBar（价格柱）

```
PriceBar:
  bar_dt: datetime         # 柱线时间戳，唯一标识
  open: int                # 开盘价（source_integer_fixed_point）
  high: int                # 最高价
  low: int                 # 最低价
  close: int               # 收盘价
  bar_index: int           # 序列位置，从 0 开始，不可变（C-17）
```

**约束**：
- 价格使用 `source_integer_fixed_point` 比较域，`/1000` 仅用于展示，不进结构计算
- `bar_index` 由上游排序后分配，Core 层不修改（C-17）
- 价格比较使用严格 `<` 和 `>`，相等不触发任何事件（C-02）

### D2 Pivot（极值点）

```
Pivot:
  pivot_type: "H" | "L"    # 极值类型
  extreme_bar_dt: datetime  # 极值所在 bar 的时间戳
  extreme_price: int        # 极值价格
  confirm_bar_dt: datetime  # 确认 bar 的时间戳（k=2 延迟）
  confirm_price: int        # 确认 bar 对应价格（H 用 high，L 用 low）
```

**检测规则**（分形 k=2）：
- H pivot：一根 bar 的 high 严格大于其左右各 2 根 bar 的 high
- L pivot：一根 bar 的 low 严格小于其左右各 2 根 bar 的 low
- 确认发生在 `extreme_bar_dt + 2` 时刻（即 `confirm_bar_dt`）
- 未确认的 pivot 不进候选池

### D3 结构上下文（Structural Context）

```
StructuralContext:
  direction: "UP" | "DOWN"  # 当前结构方向
  old_wave: Wave | None     # 上一个已终止的波段
  current_wave: Wave | None # 当前 alive 波段（UP_ALIVE / DOWN_ALIVE 时非空）
  transition: Transition | None  # 当前过渡期（TRANSITION 时非空）
```

### D4 Primitive（原语）

```
Primitive:
  start_pivot: Pivot       # 起点 pivot
  end_pivot: Pivot         # 终点 pivot
  direction: "UP" | "DOWN" # 原语方向
  span_bars: int           # 跨越的 bar 数（start_pivot.extreme_bar_dt 到 end_pivot.extreme_bar_dt）
```

### D5 Wave（波段）

```
Wave:
  wave_id: str | None      # 波段唯一标识（L4-1 生成规则）
  direction: "UP" | "DOWN" # 波段方向
  birth_type: "initial" | "continuation" | "reversal"
  pivots: list[Pivot]      # 波段内已确认 pivot（按时间顺序）
  progress_extreme_price: int  # 推进极值价格（UP 用最高 H，DOWN 用最低 L）
  progress_extreme_bar_dt: datetime  # 推进极值所在 bar
  guard_price: int         # 守护点价格
  guard_bar_dt: datetime   # 守护点所在 bar
  start_bar_dt: datetime   # 波段起始 bar
  bar_count: int           # 波段持续的 bar 数
  break_bar_dt: datetime | None  # 触发 break 的 bar（已终止时非空）
  break_price: int | None  # break 触发价格
```

### D6 上涨结构（UP Structure）

上涨结构的方向为 UP。Core 状态机在 UP_ALIVE 状态下：
- 新 H pivot 更新 `progress_extreme_price`（D16 Progress Confirmation）
- 新 L pivot 更新 `guard_price`（D9 Guard Update）
- 当某根 bar 的 `low < guard_price` 时触发 break，进入 TRANSITION

### D7 下跌结构（DOWN Structure）

下跌结构的方向为 DOWN。Core 状态机在 DOWN_ALIVE 状态下：
- 新 L pivot 更新 `progress_extreme_price`（D16 Progress Confirmation）
- 新 H pivot 更新 `guard_price`（D9 Guard Update）
- 当某根 bar 的 `high > guard_price` 时触发 break，进入 TRANSITION

### D8 Guard（守护点）

守护点是 alive 波段中最近的回撤 pivot：
- UP_ALIVE：最近确认的 L pivot 的 extreme_price
- DOWN_ALIVE：最近确认的 H pivot 的 extreme_price

**D9 守护唯一性铁律**：Guard 是单元素栈。新回撤 pivot 替换旧 guard，不保留历史。alive 期间 guard 只能被回撤 pivot 更新，不能被 progress pivot 更新。

### D10 Break（结构破坏）

当价格穿透 guard 时触发：
- UP_ALIVE：`bar.low < guard_price`（严格小于）
- DOWN_ALIVE：`bar.high > guard_price`（严格大于）

**C-05**：触发 break 的 bar 的极值（high/low）不进入 candidate pool。break bar 的 extreme 可能是新 wave 的 pivot extreme，但 break bar 自身不形成 candidate。

### D11 Transition（过渡期）

break 后进入的中间状态：
- `direction` 等于旧 wave 的 direction（不变量 4）
- 双边界模型：`boundary_high`（上边界）和 `boundary_low`（下边界）
- 边界值由 `_calculate_boundaries()` 在 break 触发时计算，使用旧 wave 的 progress 和 guard

### D12 Transition Boundary High（过渡上边界）

```
boundary_high = UP_ALIVE break 时：旧 wave 的 progress_extreme_price
                DOWN_ALIVE break 时：旧 wave 的 guard_price
```

### D13 Transition Boundary Low（过渡下边界）

```
boundary_low = UP_ALIVE break 时：旧 wave 的 guard_price
               DOWN_ALIVE break 时：旧 wave 的 progress_extreme_price
```

### D14 Candidate（候选 pivot）

Transition 内部形成的新 pivot。候选规则：
- 新 pivot 的 `extreme_bar_dt != break_bar_dt`（C-05：break bar 极值不进候选）
- 同向候选替换：同方向的新 candidate 替换旧 candidate（T5）
- 反向候选不替换同向候选，但参与 new wave 确认判定

### D15 Candidate Guard（候选守护点）

Transition 内的 candidate 形成后，若出现反向 pivot，该反向 pivot 成为 candidate guard：
- 等价于 Core 状态机使用 `_transition_guard_high` 和 `_transition_guard_low`

### D16 Progress Confirmation（推进确认）

alive 状态下，新 H pivot（UP_ALIVE）或新 L pivot（DOWN_ALIVE）更新 `progress_extreme_price`：
- UP_ALIVE：新 H pivot 的 `extreme_price > 当前 progress_extreme_price` 时更新
- DOWN_ALIVE：新 L pivot 的 `extreme_price < 当前 progress_extreme_price` 时更新
- 更新同时刷新 `progress_extreme_bar_dt`

### D17 过渡期原语归属

Transition 内形成的 pivot 和 primitive 属于新波上下文，不追加到旧 wave。旧 wave 在 break 时已冻结。

### D18 新波初始 pivot

New wave 确认后，confirmation pivot 成为新波的第一个 pivot。新波的 `progress_extreme_price` 和 `guard_price` 在下一根 bar 处理时按 Pivot 检测规则更新。

---

## §3 状态机

### 状态枚举

```
SystemState:
  UNINITIALIZED   # 初始状态，尚未收到足够 bar 检测 pivot
  UP_ALIVE        # 上涨波段存活中
  DOWN_ALIVE      # 下跌波段存活中
  TRANSITION      # 过渡期（break 后，new wave 确认前）
```

### 状态转换

```
UNINITIALIZED ──(首次 pivot 确认)──> UP_ALIVE 或 DOWN_ALIVE

UP_ALIVE ──(bar.low < guard_price)──> TRANSITION
DOWN_ALIVE ──(bar.high > guard_price)──> TRANSITION

TRANSITION ──(双条件满足)──> UP_ALIVE 或 DOWN_ALIVE（new wave）
```

### 事件顺序（O2）

每根 bar 处理时，按以下严格顺序执行：

1. **Pivot 检测**：检查当前 bar 是否确认了新的 pivot（k=2 延迟）
2. **Guard Break 检查**：检查当前 bar 是否穿透 guard（alive 状态下）
3. **Progress 更新**：若 alive 且未 break，检查新 pivot 是否推进 progress（D16）
4. **Guard 更新**：若 alive 且未 break，检查新 pivot 是否更新 guard（D9）
5. **Transition 演化**：若在 TRANSITION 状态，处理 candidate 和 new wave 确认
6. **快照生成**：生成当前 bar 的结构快照

---

## §4 初始化

### 初始 pivot 检测

等待首次确认 pivot（k=2 延迟）。确认后：

- 若首个确认为 H pivot → 进入 `UP_ALIVE`
  - `progress_extreme_price = H.extreme_price`
  - `guard_price = 0`（等待首个 L pivot 设置）
  - `guard_bar_dt = None`
- 若首个确认为 L pivot → 进入 `DOWN_ALIVE`
  - `progress_extreme_price = L.extreme_price`
  - `guard_price = 无穷大`（等待首个 H pivot 设置）
  - `guard_bar_dt = None`

### 初始候选重置（O6）

进入 alive 状态后，所有 transition 候选清空。`transition_candidate` 和 `transition_guard` 均为 None。

---

## §5 状态行为

### UP_ALIVE 状态

每根 bar 处理后：

1. **Pivot 检测**：检测新确认的 pivot
2. **Guard Break 检查**：若 `bar.low < guard_price`（严格小于），触发 break
   - 记录 `break_bar_dt`、`break_price = bar.low`
   - 调用 `_calculate_boundaries()` 计算双边界
   - 进入 TRANSITION
3. **Progress 更新**（D16）：若新确认 H pivot 且 `H.extreme_price > progress_extreme_price`（严格大于），更新 `progress_extreme_price` 和 `progress_extreme_bar_dt`
4. **Guard 更新**（D9）：若新确认 L pivot，替换 `guard_price` 和 `guard_bar_dt`
5. **bar_count 递增**

### DOWN_ALIVE 状态

每根 bar 处理后：

1. **Pivot 检测**：检测新确认的 pivot
2. **Guard Break 检查**：若 `bar.high > guard_price`（严格大于），触发 break
   - 记录 `break_bar_dt`、`break_price = bar.high`
   - 调用 `_calculate_boundaries()` 计算双边界
   - 进入 TRANSITION
3. **Progress 更新**（D16）：若新确认 L pivot 且 `L.extreme_price < progress_extreme_price`（严格小于），更新 `progress_extreme_price` 和 `progress_extreme_bar_dt`
4. **Guard 更新**（D9）：若新确认 H pivot，替换 `guard_price` 和 `guard_bar_dt`
5. **bar_count 递增**

### TRANSITION 状态

每根 bar 处理后：

1. **Pivot 检测**：检测新确认的 pivot
2. **Candidate 更新**：若新 pivot 的 `extreme_bar_dt != break_bar_dt`（C-05），处理 candidate
   - 同向：替换 candidate
   - 反向：设置 candidate guard
3. **New Wave 确认**（T6 双条件）：
   - 条件 1：active candidate 存在
   - 条件 2：candidate 突破对应边界
     - UP candidate：`candidate.extreme_price > boundary_high`（严格大于）
     - DOWN candidate：`candidate.extreme_price < boundary_low`（严格小于）
   - 双条件满足 → `_enter_new_wave()`
4. **bar_count 不递增**（transition 期间 bar_count 为 None）

---

## §6 Transition 候选管理

### Candidate 替换规则（T5）

- 同向 candidate 替换：新 candidate 替换旧 candidate，旧 candidate 丢弃
- 反向 candidate 不替换：设置 candidate guard，等待后续确认

### Candidate Guard 规则

- UP candidate 存在时，新确认的 L pivot 成为 `candidate_guard_low`
- DOWN candidate 存在时，新确认的 H pivot 成为 `candidate_guard_high`

### New Wave 确认（T6）

双条件同时满足：
1. 存在 active candidate（`candidate_pivot is not None`）
2. 该 candidate 的 `extreme_price` 突破对应 transition boundary
   - UP candidate：`extreme_price > boundary_high`
   - DOWN candidate：`extreme_price < boundary_low`

满足后调用 `_enter_new_wave()`：
- 新 wave 的 `birth_type` 由确认方向与旧 wave 方向决定
- 旧 wave 冻结，不再修改
- 新 wave 使用 confirmation pivot 作为第一个 pivot
- 新 wave 进入对应的 alive 状态（UP candidate → UP_ALIVE，DOWN candidate → DOWN_ALIVE）
- bar_count 重置为 1

---

## §7 定理（T1-T9）

### T1 结构二分定理

任意时刻，市场结构必属于以下二者之一：
- 一个 alive 波段（UP_ALIVE 或 DOWN_ALIVE）
- 一个 transition（两波之间的过渡期）

不存在"无结构"状态（UNINITIALIZED 仅在数据不足时存在）。

### T2 推进-守护配对定理

每个 alive 波段由一对数值定义：
- 推进极值（progress_extreme_price）：波段方向上的最远价格
- 守护点（guard_price）：波段方向上的最近回撤价格

二者共同定义波段的结构边界。

### T3 Break 终止定理

当价格穿透守护点时，当前波段终止。break 是不可逆的——旧波不可复活（不变量 4）。

### T4 旧波不可复活定理

一旦 break 发生，旧波段进入冻结状态。transition 内形成的任何 pivot 都属于新波上下文，不追加到旧波。

### T5 Candidate 最新有效定理

transition 内，同方向的新 candidate 替换旧 candidate。任何时候最多只有一个 active candidate 和一个 candidate guard。

### T6 新波双条件确认定理

新波确认需要同时满足：
1. 存在 active candidate（同向 pivot）
2. 该 candidate 突破 transition boundary

仅有 candidate 不足够；仅有 boundary 突破也不足够。

### T7 Break 后新波创建定理

break 发生后，transition 内部必然通过 T6 双条件创建新波。不存在"永久 transition"——任意 bar 序列最终都会确认新波。

（注：T7 是理论保证。实践中极长的 transition 可能存在，但逻辑上必然终结。）

### T8 Transition 非波段定理

transition 不是波段。它没有 direction（继承旧波方向仅用于上下文）、没有 progress、没有 guard。它只是一个"候选池"。

### T9 口头状态可消除定理

所有"口头状态"（如"加速中"、"停滞中"、"压力中"）都可以通过 Core 的结构事实（progress 价格、guard 价格、bar_count、transition 边界）推导出来，不必作为 Core 的独立状态。

---

## §8 快照（Snapshot）

### 结构快照

每根 bar 处理后生成不可变快照（C-18）：

```
CoreSnapshot:
  bar_dt: datetime
  bar_index: int
  system_state: SystemState
  direction: "UP" | "DOWN" | None
  progress_extreme_price: int | None
  progress_extreme_bar_dt: datetime | None
  guard_price: int | None
  guard_bar_dt: datetime | None
  bar_count: int | None
  break_bar_dt: datetime | None
  break_price: int | None
  transition_boundary_high: int | None
  transition_boundary_low: int | None
  candidate_pivot: Pivot | None
  candidate_guard_high: int | None
  candidate_guard_low: int | None
  rule_versions: dict[str, str]
```

**不可变性**（C-18）：快照一旦生成，不可修改。下游不能写回快照字段。

---

## §9 操作边界（O1-O8）

以下八条规则从 v1.4 操作边界规则集成。它们是 Core 状态机的施工铁律。

### O1 Pivot 规则版本

pivot 检测使用分形 k=2 规则。规则版本固定为 `fractal_k2_v1.0`。

### O2 事件顺序

每根 bar 内的事件按严格顺序处理（§3 事件顺序）。事件顺序不可重排——任何重排都会改变状态机结果。

### O3 严格比较

所有价格比较使用严格 `<` 和 `>`：
- break：`bar.low < guard_price` 或 `bar.high > guard_price`
- progress：`H.extreme_price > progress_extreme_price` 或 `L.extreme_price < progress_extreme_price`
- boundary：`candidate.extreme_price > boundary_high` 或 `candidate.extreme_price < boundary_low`
- 相等不触发任何事件

### O4 Candidate 刷新

transition 内同向 candidate 替换时，旧 candidate 丢弃。仅保留最新 candidate。

### O5 Transition Primitive 上下文

transition 内形成的 pivot 和 primitive 使用 transition 上下文，不更新旧 wave。旧 wave 在 break 时已冻结。

### O6 初始候选重置

每次进入 alive 状态时，transition 候选全部清空。避免残留上轮候选。

### O7 快照合同

每根 bar 处理后生成一个快照。快照字段不可变。快照包含 rule_versions 记录所有参与计算的规则版本。

### O8 Replay 确定性

相同的 PriceBar 序列 → 相同的快照序列（逐字段相同）。不包括 `runtime_fingerprint`（用于诊断，不参与语义）。

---

## §10 不变量

| # | 不变量 | 来源 |
|---|--------|------|
| 1 | 所有价格比较使用严格 `>` / `<`，相等不触发 | O3, C-02 |
| 2 | guard 是单元素栈，alive 期间仅被回撤 pivot 替换 | D9 |
| 3 | 旧波 break 后不可复活，transition 内 pivot 不追加到旧波 | T4, O5 |
| 4 | transition 内 direction = 旧波 direction | D11 |
| 5 | new wave 确认需双条件（active candidate + 突破边界） | T6 |
| 6 | break 判定使用 bar.low（UP）或 bar.high（DOWN） | D10 |
| 7 | UNINITIALIZED 状态下不产生 break | O6 |
| 8 | 每根 bar 产生一个不可变快照，含 rule_versions | O7, C-18 |

---

## §11 编号对照

Definitive v2.0 的 D1-D18 编号在 v2.1 中完全保留。D3（结构上下文）、D6（上涨结构）、D7（下跌结构）在 v2.0 正文中编号跳跃，v2.1 恢复完整编号。

| 编号 | 名称 | 状态 |
|------|------|------|
| D1 | PriceBar | 不变 |
| D2 | Pivot | 不变 |
| D3 | 结构上下文 | 恢复 |
| D4 | Primitive | 不变 |
| D5 | Wave | 不变 |
| D6 | 上涨结构 | 恢复 |
| D7 | 下跌结构 | 恢复 |
| D8 | Guard | 不变 |
| D9 | 守护唯一性铁律 | 不变 |
| D10 | Break | 不变 |
| D11 | Transition | 不变 |
| D12 | Transition Boundary High | 不变 |
| D13 | Transition Boundary Low | 不变 |
| D14 | Candidate | 不变 |
| D15 | Candidate Guard | 不变 |
| D16 | Progress Confirmation | 恢复（补丁还原） |
| D17 | 过渡期原语归属 | 恢复（补丁还原） |
| D18 | 新波初始 pivot | 不变 |

定理 T1-T9 编号不变。O1-O8 编号不变。

---

## §12 测试覆盖要求

### 核心不变量测试（必须覆盖）

| 测试类别 | 最少测试数 | 覆盖内容 |
|---------|----------|---------|
| 初始化 | 3 | UNINITIALIZED → UP_ALIVE、UNINITIALIZED → DOWN_ALIVE、首次 pivot 确认 |
| Guard break | 4 | UP_ALIVE break、DOWN_ALIVE break、相等不触发、break 后进入 TRANSITION |
| Transition 候选 | 4 | 候选创建、同向替换、反向不替换、break bar 极值不进候选 |
| New wave 确认 | 3 | 双条件满足、仅 candidate 不满足、仅 boundary 突破不满足 |
| D9 Guard 更新 | 2 | UP_ALIVE guard 替换、DOWN_ALIVE guard 替换 |
| D16 Progress 更新 | 2 | HH 推进、LL 推进 |
| O8 Replay 确定性 | 2 | 相同输入→相同输出、不同输入→不同输出 |

### 边界情况测试（必须覆盖）

| 测试类别 | 最少测试数 |
|---------|----------|
| 空输入 | 1 |
| 单根 bar | 1 |
| 全同价格（无 pivot） | 1 |
| 极限值相等（严格不等式） | 2 |

### 当前状态

Core 层 47 个测试已覆盖以上所有类别。