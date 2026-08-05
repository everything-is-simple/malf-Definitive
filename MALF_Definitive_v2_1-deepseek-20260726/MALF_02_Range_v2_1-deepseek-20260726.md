# MALF v2.1 Range — 震荡区间一等公民

> 层：L1b — Range（震荡区间）
>
> 基于：v2.0 Range（claude-20260616）+ IMPLEMENTATION-CONTRACT-PATCH R-05
>
> 作者：DeepSeek
>
> 日期：2026-07-26

---

## §1 层职责

Range 层将 Core 的 transition（中间未决态）升格为"一等公民"结构对象。Range 有：
- 自己的上下边界（可从 init 值演化）
- 自己的生命周期（从 break 开始，到 resolution 结束）
- 自己的户口（在 Lifespan 层有自己的排名池）
- 自己的分类（continuation / reversal）

Range 层不修改 Core 状态机。Core 使用的是 boundary_init 值（冻结），Range 层在 boundary_init 基础上允许演化。

---

## §2 Range 对象

```
Range:
  range_id: str | None
  break_bar_dt: datetime          # 触发 break 的 bar（Range 起点）
  break_price: int                # break 触发价格
  old_wave_direction: "UP" | "DOWN"
  
  # 边界（init 值 = Core 计算的 transition boundary）
  boundary_high_init: int         # 上边界初始值（来自 Core）
  boundary_low_init: int          # 下边界初始值（来自 Core）
  boundary_high_now: int          # 上边界当前值（可演化，R3）
  boundary_low_now: int           # 下边界当前值（可演化，R3）
  
  # 演化统计
  evolution_count: int            # 边界演化次数（high_now 或 low_now 变化的次数）
  pivot_count: int                # Range 内形成的 pivot 数量
  candidate_replacement_count: int  # candidate 被替换的次数（同向替换）
  
  # 结束
  resolution_bar_dt: datetime | None  # 突破边界确认的 bar
  resolution_type: "up" | "down" | None  # 突破方向
  resolution_price: int | None     # 突破价格
  span_bars: int | None            # 总跨度（break_bar_dt 到 resolution_bar_dt）
  
  # 分类
  range_type: "continuation" | "reversal" | None
```

---

## §3 Boundary 演化（R3）

### 两层边界模型

**重要**：Range 使用两层边界，服务于不同目的：

| 边界 | 持有者 | 可否演化 | 用途 |
|------|--------|---------|------|
| `boundary_high_init` / `boundary_low_init` | Core + Range | 不可变 | Core 状态机做 new wave 确认判定 |
| `boundary_high_now` / `boundary_low_now` | Range | 可演化 | Range 统计（resolution_distance_pct 等） |

### 边界使用场景对照表

**实现者必须遵循以下对照表**。混用 init 和 now 会导致 Core 状态机行为不稳定或 Range 统计失真。

| 使用场景 | 使用的边界 | 理由 |
|---------|-----------|------|
| Core 状态机 new wave 确认判定（T6 双条件） | `boundary_high_init` / `boundary_low_init` | 状态机稳定性。判定边界在 break 时冻结，不可随演化变化 |
| Range resolution_distance_pct 计算 | `boundary_high_now` / `boundary_low_now` | 反映真实震荡范围。演化后的边界更准确 |
| Range boundary 演化（R3） | `boundary_high_now` / `boundary_low_now` | 演化发生在 now 值上 |
| Lifespan 统计（resolution_distance_rank） | `boundary_high_now` / `boundary_low_now` | 统计真实特征，使用演化后的值 |
| 快照输出（transition_boundary_high/low） | `boundary_high_init` / `boundary_low_init` | 快照报告 Core 判定使用的边界，保持可审计性 |
| 快照输出（range_boundary_high_now/low_now） | `boundary_high_now` / `boundary_low_now` | 单独字段报告 Range 的当前边界 |

### 演化规则

Transition 内每确认一个新 pivot，检查是否扩展 boundary：

- 上边界扩展：新 pivot 的 `extreme_price > boundary_high_now`（严格大于）→ 更新 `boundary_high_now`
- 下边界扩展：新 pivot 的 `extreme_price < boundary_low_now`（严格小于）→ 更新 `boundary_low_now`
- 每次更新 `evolution_count += 1`

**仅使用已确认 pivot**。未确认的 pivot 不参与 boundary 演化。

---

## §4 Resolution（R4）

当 T6 双条件满足（new wave 确认）时，Range 结束：

- `resolution_bar_dt = confirmation_pivot.confirm_bar_dt`
- `resolution_type = "up"`（UP candidate 突破 boundary_high）或 `"down"`（DOWN candidate 突破 boundary_low）
- `resolution_price = confirmation_pivot.extreme_price`
- `span_bars = resolution_bar_dt 到 break_bar_dt 的 bar 数`

---

## §5 Resolution Distance（R5）

```
resolution_distance_pct:
  up 突破：  (confirmation_pivot.extreme_price - boundary_high_now) / boundary_high_now
  down 突破：(boundary_low_now - confirmation_pivot.extreme_price) / boundary_low_now
```

**定义明确**：
- `confirmation_pivot.extreme_price`：确认 pivot 的 extreme_price（H pivot 用 high，L pivot 用 low）
- 不是 confirmation bar 的 high/low，是 pivot 的价格
- 使用 `boundary_high_now` / `boundary_low_now`（演化后的当前值），不是 init 值

`resolution_distance_pct` 为正值表示"突破幅度"，值越大表示突破越有力。可正可负（当 boundary 演化后突破价格未超出演化后的边界时）。

---

## §6 Range Type 分类（R6）

```
range_type:
  old_wave = UP, resolution = up   → continuation_range
  old_wave = UP, resolution = down → reversal_range
  old_wave = DOWN, resolution = down   → continuation_range
  old_wave = DOWN, resolution = up → reversal_range
```

> ⚠️ **命名陷阱 —— 实现者必读**：
>
> `continuation_range` 的 "continuation" 延续的是 **break 方向**，不是旧 wave 方向！
>
> - 旧 up wave 被向下 break 后，最终向下突破 → `continuation_range`（延续了 break 的下行方向）
> - 旧 up wave 被向下 break 后，最终向上突破 → `reversal_range`（反转了 break 的下行方向）
> - 旧 down wave 被向上 break 后，最终向上突破 → `continuation_range`（延续了 break 的上行方向）
> - 旧 down wave 被向上 break 后，最终向下突破 → `reversal_range`（反转了 break 的下行方向）
>
> 如果你读到 "continuation" 以为延续的是旧 wave 方向，你会理解反。**continuation = 延续 break 方向，reversal = 反转 break 方向。**

---

## §7 不变量

| # | 不变量 |
|---|--------|
| R1 | Range 的 boundary_init 值来自 Core 的 transition boundary，不可变 |
| R2 | Range 的 boundary_now 值基于 boundary_init 演化，仅使用已确认 pivot |
| R3 | Range 演化不修改 Core 状态机使用的 boundary 值 |
| R4 | Range 在 resolution 时冻结，不可再演化 |
| R5 | continuation_range 和 reversal_range 分池统计（Lifespan 层） |

---

## §8 编号对照

R1-R8 编号与 v2.0 一致。R5（resolution_distance_pct）的公式在 v2.1 中明确了 `confirmation_pivot.extreme_price` 的定义。R6 的命名增加了警告。

---

## §9 测试覆盖要求

### 核心不变量测试（必须覆盖）

| 测试类别 | 最少测试数 | 覆盖内容 |
|---------|----------|---------|
| Range 创建 | 2 | UP break 后 Range 创建、DOWN break 后 Range 创建 |
| Boundary 初始化 | 2 | boundary_init 与 Core transition boundary 一致 |
| Boundary 演化 | 3 | 上边界扩展、下边界扩展、不扩展（价格在区间内） |
| Resolution 判定 | 4 | up resolution、down resolution、continuation_range、reversal_range |
| Resolution distance | 2 | 正 distance、负 distance（boundary 演化后价格未超出） |
| 两层边界分离 | 2 | Core 用 init 值、Range 用 now 值 |

### 边界情况测试（必须覆盖）

| 测试类别 | 最少测试数 |
|---------|----------|
| 无演化（transition 内无新 pivot） | 1 |
| 单 pivot 演化 | 1 |
| 多次演化 | 1 |
| 演化后 resolution | 1 |