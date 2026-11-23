# MALF 版本演化史

**创建日期**: 2026-11-23  
**目的**: 记录从v1.0到v3.0的演化路径和原因

---

## 📊 版本总览

| 版本 | 日期 | 文件数 | 核心变化 | 状态 |
|------|------|--------|---------|------|
| **v1.0** | 2026-08-05前 | 1文字+4PDF | 图解版，最简洁 | ✅ 核心基础 |
| **v1.2** | 2026-08-05后 | 4个MD | 分层：Core/Lifespan/Service | 📦 工程化 |
| **v1.3** | 时间未知 | 8个MD | 修正break/transition逻辑 | 📦 精确化 |
| **v1.4** | 时间未知 | 9个MD | 加入边界规则 | 📦 完善化 |
| **v1.5** | 时间未知 | 9个MD | 行为bucket | 📦 细化 |
| **v2.0** | 2026-06-16 | 6个MD | Definitive重构 | 📦 claude版 |
| **v2.1** | 2026-07-26 | 5个MD | Structural Position | 📦 deepseek版 |
| **v3.0** | 2026-11-23 | 1个MD | 回归v1.0核心 | ✅ 最小必要集 |

---

## 🎯 v1.0 → v1.2: 分层工程化

### 升级原因

**问题**: v1.0是单一整体，从价格到统计到服务全在一起

**解决**: 分成三层，职责分离

```
v1.0 (1个文件):
  price bars → 结构 → 统计 → 服务 (全混在一起)

v1.2 (3+1个文件):
  01_Core: 结构如何成立、终止、转换
  02_Lifespan: 波段如何被统计、比较、定位
  03_Service: MALF如何服务系统其它模块
  00_Bridge: 总纲与关联图
```

### 关键修正 (来自v1.2 Bridge)

| 评审问题 | 修正位置 | 修正结果 |
|---------|---------|---------|
| transition中candidate方向切换规则缺失 | Core D15/T5 | 最新candidate guard决定唯一active candidate |
| candidate context reference H/L来源不明确 | Core D13/D16 | transition中使用old wave最终progress extreme |
| transition中direction表述不一致 | Lifespan L13 | transition中direction=old_direction |

### 新增内容

- **分层架构**: Core → Lifespan → Service
- **数据流**: pivot → structure → wave → break → transition → candidate
- **反向依赖禁止**: Core不依赖Lifespan, Lifespan不依赖Alpha

---

## 🔧 v1.2 → v1.3: 精确化

### 升级原因

**问题**: v1.2中三个容易误解的权威定义问题

```
1. break(up wave) = break(HL) 没有明确是哪一个HL
2. "candidate方向 + confirmed" 这类旧式缩写混淆了candidate与new wave confirmation
3. old_progress_extreme_price单点reference无法严谨覆盖same/opposite-direction
```

### 解决方案

**重写Core主轴**:
```
PriceBar
-> Confirmed H/L
-> HH/HL/LL/LH
-> Active Wave
-> Current Effective Guard      ← 明确：当前有效守护点
-> Break
-> Transition Boundary
-> Active Candidate Guard
-> Progress Confirmation
-> New Wave
```

### 关键裁决

**裁决1: Break的guard是"当前有效guard"**
```text
current_effective_HL = active up wave内最新确认且仍有效的HL
current_effective_LH = active down wave内最新确认且仍有效的LH

break(up wave)   = price breaks current_effective_HL
break(down wave) = price breaks current_effective_LH
```

**裁决2: Candidate ≠ Confirmation**
- candidate: 候选守护点
- confirmation: 推进确认（新波真正成立）
- 不再混用

### 新增内容

- **图表版**: 04_Core_Chart, 05_Lifespan_Chart, 06_Service_Chart
- **审计文档**: 07_Definition_Theorem_Review

---

## 📏 v1.3 → v1.4: 边界规则

### 升级原因

**问题**: 实现中遇到边界case不清楚

**解决**: 新增 `01B_Core_Operational_Boundary_Rules`

### 新增内容

- **边界规则文档**: 专门处理edge case
- 文件数: 8 → 9

---

## 🎨 v1.4 → v1.5: 行为bucket

### 升级原因

**问题**: 只有结构位置，缺少行为刻画

**解决**: 在Core侧新增对既有结构状态的行为刻画

### 新增对象 (v1.5 Core)

**定义C1: continuation_regime**
```text
描述当前wave的延续行为bucket:
- advancing
- slowing
- stalled
- transitioning
```

**定义C2: boundary_pressure_regime**
```text
描述当前结构更靠近哪类边界:
- continuation_side
- guard_pressure
- transition_pressure
- neutral
```

**定义C3: directional_continuity_regime**
```text
描述当前结构表现为:
- same_direction_continuation
- opposite_direction_rebirth
- transition_unresolved
```

### 核心定理

```text
1. 行为bucket只能基于MALF已确认结构事实
2. transition仍然不是wave
3. wave_behavior_snapshot不得让旧wave复活
4. 没有lineage的行为bucket不得进入正式快照
```

---

## 🌊 v1.5 → v2.0: Definitive重构 (claude版)

### 升级原因

**问题**: v1.x累积复杂，需要全面重构

**解决**: 按照Definitive规范重写

### 变化

**结构重组**:
```
v1.5 (Core + Lifespan + Service):
  01_Core
  01B_Boundary
  02_Lifespan
  03_Service
  
v2.0 (五层重构):
  01_Core
  02_Range         ← 新增
  03_Lifespan
  04_Probability   ← 新增
  05_Service
```

### 新增层级

**Range层**: 
- Range诞生 (guard break触发)
- Boundary演化
- Resolution判定
- Continuation/Reversal分类

**Probability层**:
- 概率分析
- 成功率统计

---

## 🔄 v2.0 → v2.1: Structural Position (deepseek版)

### 升级原因

**问题**: v2.0的Probability层语义模糊

**解决**: 重命名为Structural Position

### 核心变化

```
v2.0: 04_Probability
v2.1: 04_Structural_Position
```

**语义等价**: 只是清晰表达，核心逻辑不变

### 实现状态

**Sperandeo-malf-engine** (基于v2.1):
- Core层: ✅ 47 passed
- Range层: ✅ 6+1 real
- Lifespan层: ✅ 77 passed
- Structural Position层: ✅ 12 passed
- 总计: **112 passed**

---

## 🎯 v2.1 → v3.0: 回归简洁

### 升级原因

**问题**: v2.x过度复杂化，偏离v1.0的简洁精神

**目标**: 回归核心，只保留**完整交易生命状态机**所需的最小必要集

### 核心决策

**去掉的** (非核心):
- ❌ Range层 (属于扩展)
- ❌ Structural Position层 (属于扩展)
- ❌ velocity (非必需)
- ❌ continuation_regime (过度细分)
- ❌ boundary_pressure (过度细分)

**保留的** (核心):
- ✅ 7个原语 (HH/HL/LL/LH/break/new-count/no-new-span)
- ✅ 3轴寿命 (new-count/no-new-span/life-state)
- ✅ 3状态 (alive/broken/reborn)
- ✅ WavePosition输出
- ✅ v1.0的图解精神

### v3.0 = v1.0核心 + 更好组织

```
v1.0: 核心定义 + 图解 (最清晰)
v1.2-v1.5: 工程化 (分层、边界、行为)
v2.0-v2.1: 复杂化 (五层、统计、概率)
v3.0: 回归v1.0核心 + 保留工程化组织
```

---

## 📊 演化路径总结

### 主线1: 核心定义演化

```
v1.0: 单一整体 (清晰简洁)
  ↓
v1.2: 分层 (Core/Lifespan/Service)
  ↓
v1.3: 精确化 (current_effective_guard)
  ↓
v1.4: 边界规则
  ↓
v1.5: 行为bucket
  ↓
v2.0: 五层重构 (复杂化)
  ↓
v2.1: 语义优化
  ↓
v3.0: 回归v1.0核心 (简洁化)
```

### 主线2: 文件数量演化

```
v1.0: 1文字 + 4PDF
v1.2: 4 MD
v1.3: 8 MD (加图表版)
v1.4: 9 MD (加边界规则)
v1.5: 9 MD (保持)
v2.0: 6 MD (重构)
v2.1: 5 MD (精简)
v3.0: 1 MD (回归极简)
```

### 主线3: 复杂度曲线

```
复杂度 ▲
      │                    v2.0
      │                   ╱    ╲
      │          v1.5    ╱      ╲ v2.1
      │         ╱       ╱        ╲
      │   v1.4 ╱                  ╲
      │   ╱   ╱                    ╲
      │  ╱v1.3                      ╲
      │ ╱v1.2                        ╲
      │╱                              v3.0
v1.0  ●─────────────────────────────────●────► 时间
      (简洁)                        (回归简洁)
```

---

## 🎯 核心教训

### 1. 简洁的力量

**v1.0的图解版** = 最清晰的表达方式
- 一句话定义
- 五条上位原则
- 7个原语
- 3轴寿命
- 图解说明

### 2. 工程化的陷阱

**v1.2-v1.5的分层** = 有价值，但容易过度
- 分层本身很好 (Core/Lifespan/Service)
- 但容易加入非必需概念 (行为bucket)
- 边界规则有用，但不属于核心定义

### 3. 重构的风险

**v2.0-v2.1的五层** = 过度工程化
- Range层: 有价值，但不是核心
- Probability/Structural Position: 属于应用层
- 技术实现很完善 (112 passed)
- 但定义层过于复杂

### 4. 回归的智慧

**v3.0 = v1.0的精神 + v1.3的精确 + 现代组织**
- 保留v1.0的核心7原语+3轴
- 保留v1.3的current_effective_guard
- 保留v1.2的分层思想 (明确必需vs可选)
- 去除v1.5-v2.1的过度扩展

---

## 💡 未来建议

### 核心vs扩展

**核心** (必须在v3.0):
- 7原语 + 3轴 + 3状态
- WavePosition输出
- 完整生命状态机

**扩展** (可选，不在v3.0):
- Range层 (有价值，独立模块)
- 历史位置统计 (update_rank/stagnation_rank)
- 行为bucket (advancing/slowing...)
- 概率分析

### 实现vs定义

**定义** (本文件):
- 保持极简
- 只定义核心概念
- 参数可校准，定义不变

**实现** (Sperandeo-malf-engine):
- 可以实现全部五层
- 但明确哪些是核心，哪些是扩展
- 保持模块独立性

---

## 📚 权威链

| 版本 | 状态 | 用途 |
|------|------|------|
| **v1.0** | 参考 | 图解版，最清晰的表达 |
| v1.2-v1.5 | 归档 | 工程化演化过程 |
| v2.0-v2.1 | 归档 | 技术实现参考 |
| **v3.0** | 权威 | 核心最小定义 |
| Sperandeo-malf-engine | 实现 | 基于v2.1的技术实现 |

---

**状态**: 📋 演化史完成

**下一步**: 基于v3.0核心定义，明确实现边界

