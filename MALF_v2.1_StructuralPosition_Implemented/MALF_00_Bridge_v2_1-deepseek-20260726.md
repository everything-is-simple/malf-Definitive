# MALF v2.1 Bridge — v2.0 → v2.1 变更说明

> 作者：DeepSeek（基于 MALF v2.0 Definitive + IMPLEMENTATION-CONTRACT-PATCH + malf-engine 施工证据）
>
> 日期：2026-07-26
>
> 版本：v2.1
>
> 权威：Definitive。本文件是 MALF v2.1 权威定义的入口和变更说明。

---

## 0. 为什么需要 v2.1

v2.0（claude-20260616）是 MALF 的 Definitive 重构定稿。但两个事件触发了 v2.1：

1. **施工证据**：malf-engine 的 Core 层实现（5 刀、47 个测试）暴露了 v2.0 正文中的 21 条歧义和缺口，已在 IMPLEMENTATION-CONTRACT-PATCH 中裁决，但未回写正文。
2. **全版本审查**：从 v1.0 到 v2.0 的逐文件审查发现了一个命名问题（"Probability" 层不输出概率）和三处规格歧义（resolution_distance_pct 公式、R6 命名陷阱、percentile_rank 公式未入正文）。

v2.1 的目标：
- 将所有已裁决的补丁回写入正文，消灭"补丁与正文两层皮"
- 修正命名问题
- 闭合剩余歧义
- 不改变 v2.0 的语义（不新增对象、不删除层、不修改状态机）

v2.1 与 v2.0 **语义等价**。v2.1 是 v2.0 的清楚表达，不是新版本。

---

## 1. v2.0 → v2.1 变更清单

### 1.1 命名变更

| v2.0 | v2.1 | 理由 |
|------|------|------|
| Probability 层 | Structural Position 层 | 该层不输出概率，输出 rank 透传 + 向量差 + 比较标签。名字诚实了，下游期待就对了 |
| `WaveProbabilitySnapshot` | `WaveStructuralSnapshot` | 同上。对外契约的顶层类型名跟随层名变更 |

### 1.2 补丁回写（21 条）

以下 21 条裁决从 IMPLEMENTATION-CONTRACT-PATCH 回写入 v2.1 正文：

**第 1 层（勘误，4 条）**：
- D3 结构上下文：在 Core §2 基础对象表中恢复
- D6 上涨结构：在 Core §2 基础对象表中恢复
- D7 下跌结构：在 Core §2 基础对象表中恢复
- 极限值定义：在 Core §2 中明确"老波极限值 = 当前有效 HL 的极值"

**第 2 层（还原，10 条）**：
- D16 Progress Confirmation：在 Core §5 状态机中明确 alive 状态下的 HH/LL 推进逻辑
- D17 过渡期原语归属：在 Core §6 中明确
- T1-T2：在 Core §7 中恢复完整定理表述
- T7-T8：在 Core §7 中恢复
- O1-O8：在 Core §9 中集成（从 v1.4 独立文件移入 Core 正文）

**第 3 层（消歧，7 条）**：
- C-02 严格不等式：在 Core §5 中每处比较标注 `>` / `<`（不含 `=`）
- C-05 break bar 极值不进候选池：在 Core §6 中明确
- C-17 bar_index 不可变：在 Core §2 中明确
- C-18 不可变快照：在 Core §8 中明确
- S-01 中断恢复：在 Service §5 中明确
- R-05 resolution_distance_pct 公式：在 Range §5 中明确"confirmation_H_price"的定义
- O-01 事件顺序：在 Core §9 中明确

### 1.3 歧义闭合（3 条）

- **R6 continuation_range 命名**：在 Range §6 中加注，明确"continuation"延续的是 break 方向，非旧 wave 方向
- **percentile_rank 公式**：从补丁 L4-3 移入 Lifespan §4 正文
- **两层边界（Core init vs Range now）**：在 Range §3 中显式说明

### 1.4 新增诚实声明

- **新标的/新周期退化**：在 Lifespan §3 和 Structural Position §1 中明确声明
- **P4 cross_compare 噪声**：在 Structural Position §4 中加强警告
- **阈值魔法数字**：在 Structural Position §5 中标注为"待经验校准"

---

## 2. v2.1 文件结构

```
MALF_Definitive_v2_1-deepseek-20260726/
├── MALF_00_Bridge_v2_1-deepseek-20260726.md    # 本文件
├── MALF_01_Core_v2_1-deepseek-20260726.md       # Core：结构状态机（含 O1-O8）
├── MALF_02_Range_v2_1-deepseek-20260726.md      # Range：震荡区间一等公民
├── MALF_03_Lifespan_v2_1-deepseek-20260726.md   # Lifespan：双轨户口与排名
├── MALF_04_Structural_Position_v2_1-deepseek-20260726.md  # Structural Position：结构位置（原 Probability）
├── MALF_05_Service_v2_1-deepseek-20260726.md    # Service：对外接口与铁律
└── MANIFEST-deepseek-20260726.json              # 文件清单与哈希
```

---

## 3. 语义不变保证

v2.1 对 v2.0 的语义保证：

1. Core 状态机：零变更。所有状态转换、触发条件、边界值不变。
2. Range 对象：零变更。boundary 演化规则、resolution 判定不变。
3. Lifespan 排名：零变更。peer_sample 规则、rank 公式不变。
4. Structural Position 视图：零变更。四个视图的字段和计算逻辑不变（仅层名和快照类型名变更）。
5. Service 铁律：零变更。S6 不变。

v2.1 是 v2.0 的"清楚版本"，不是"新版本"。任何实现了 v2.0 的引擎，只要行为正确，就自动兼容 v2.1。

---

## 4. 与 malf-engine 的关系

malf-engine 当前实现了 v2.0 Core 层（5 刀、47 个测试）。v2.1 的 Core 正文完全兼容当前实现。

需要更新的代码层面：
- 类型名 `WaveProbabilitySnapshot` → `WaveStructuralSnapshot`（可在第六刀时统一重命名）
- 文档引用中的"Probability" → "Structural Position"

不需要更新的：
- 所有状态机逻辑
- 所有测试预期
- 所有 fixture 数据

---

## 5. 权威链

v2.1 的裁决权威：

1. 本 Bridge 文件
2. v2.1 Core / Range / Lifespan / Structural Position / Service 正文
3. v2.0 Definitive（claude-20260616）——作为语义等价参考
4. IMPLEMENTATION-CONTRACT-PATCH ——补丁记录，已全部回写，不再独立权威
5. v1.4 操作边界规则 ——O1-O8 已集成入 v2.1 Core §9，不再独立权威

发生冲突时：v2.1 正文 > v2.0 正文 > 补丁 > v1.4 操作边界。

---

## 6. 实现状态对照

v2.1 各层与 malf-engine 当前实现的对照：

| 层 | v2.1 章节 | 当前实现状态 | 测试数量 | 下一步工作 |
|-----|---------|------------|---------|----------|
| Core | §1-§10 | 完成（5 刀） | 47 passed | — |
| Range | §1-§8 | 未开始 | 0 | 第六刀：实现 Range 对象、boundary 演化、resolution 判定 |
| Lifespan | §1-§7 | 未开始 | 0 | 第七刀：实现双轨 peer_sample、percentile_rank |
| Structural Position | §1-§9 | 未开始 | 0 | 第八刀：实现 4 视图计算、标签规则 |
| Service | §1-§8 | 部分（snapshot 结构已定义） | 0 | 第九刀：实现 usage 判定、持久化、中断恢复 |

**当前完成的 Core 层覆盖**：
- 初始化逻辑（UNINITIALIZED → UP_ALIVE / DOWN_ALIVE）
- Pivot 检测（分形 k=2，延迟确认）
- Guard break 检测（同向突破，严格不等式）
- Transition 演化（candidate 跟踪、替换、new wave 确认）
- D9 Guard 更新（回撤 pivot 替换 guard）
- D16 Progress Confirmation（HH/LL 推进）
- Wave bar_count 计算
- O8 Replay 确定性验证

---

## 7. 性能基准

以下为设计目标，非验收条件：

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 单 bar 处理时间 | < 10ms | 单 symbol、单 timeframe，Core 层计算 |
| 全链路快照时间 | < 50ms | Core + Range + Lifespan + Structural Position |
| peer_sample 内存 | < 100MB | 假设 10 年日线、每 symbol 约 1200 个 terminated wave |
| 快照存储增长 | < 5MB/年/symbol | JSON Lines 格式，每 bar 一个快照 |
| replay 验证开销 | < 2x | 两遍计算 + 逐字段比对 |

---

## 8. 版本治理

### v2.1 批准

- 版本号：v2.1
- 作者：DeepSeek
- 审查：Claude（2026-07-26 审查通过，提出 14 条修订建议，已全部处理）
- 状态：Definitive

### 后续变更流程

1. **提案**：任何对 v2.1 的语义变更（新增对象、修改状态机、增删字段）需先在 IMPLEMENTATION-CONTRACT-PATCH 或新 ISSUE 中提案
2. **审查**：至少一人（人类或 AI）审查，确认：
   - 与 v2.1 的语义兼容性
   - 所有受影响的不变量和测试
3. **版本号**：
   - 勘误（不改变语义）：v2.1.1, v2.1.2, ...（在 MANIFEST 中记录）
   - 语义变更（新增/修改/删除）：v2.2, v2.3, ...（需新 Bridge 文件）
   - 重大重写：v3.0（需全新 Definitive 目录）
4. **禁止碎片化**：不允许出现 v2.1.1-alpha、v2.1.1-beta 等非正式版本号
5. **紧急勘误**：如发现严重歧义或错误，可直接修订正文并在 MANIFEST 中记录勘误日期和内容，不升级版本号