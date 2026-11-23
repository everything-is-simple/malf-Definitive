# MALF 版本命名指南

**创建日期**: 2026-11-23  
**目的**: 通过目录名就能看出版本的核心变化

---

## 📋 命名规则

```
MALF_v{版本号}_{核心变化}_{次要特征}
```

**原则**:
- 版本号保持不变
- 核心变化用1-2个词概括
- 看名字就知道改了什么

---

## 📂 新命名 → 含义

### v1.0 系列

| 新名称 | 核心变化 | 说明 |
|--------|---------|------|
| `MALF_v1.0_GraphicCore_SingleFile` | 图解核心，单文件 | 最简洁，4个PDF图解 |
| `MALF_v1.2_ThreeLayer_Split` | 三层分离 | Core/Lifespan/Service分层 |
| `MALF_v1.3_GuardPrecision_Charts` | 守护点精确化+图表 | current_effective_guard明确 |
| `MALF_v1.4_BoundaryRules` | 边界规则 | 加入边界case处理 |
| `MALF_v1.5_BehaviorBucket` | 行为bucket | 加入延续/停滞行为描述 |

### v2.0 系列

| 新名称 | 核心变化 | 说明 |
|--------|---------|------|
| `MALF_v2.0_FiveLayer_Range_Probability` | 五层+Range+概率 | 重构为五层架构 |
| `MALF_v2.1_StructuralPosition_Implemented` | 结构位置+已实现 | Probability改名，有实现 |

---

## 🔄 旧名称 → 新名称对照

```
旧: MALF_Three_Part_Design_Set_v1_0
新: MALF_v1.0_GraphicCore_SingleFile
变化: 图解核心，单文件

旧: MALF_Three_Part_Design_Set_v1_2
新: MALF_v1.2_ThreeLayer_Split
变化: 三层分离

旧: MALF_Three_Part_Design_Set_v1_3
新: MALF_v1.3_GuardPrecision_Charts
变化: 守护点精确化+图表

旧: MALF_Three_Part_Design_Set_v1_4
新: MALF_v1.4_BoundaryRules
变化: 边界规则

旧: MALF_Three_Part_Design_Set_v1_5
新: MALF_v1.5_BehaviorBucket
变化: 行为bucket

旧: MALF_Definitive_v2_0-claude-20260616
新: MALF_v2.0_FiveLayer_Range_Probability
变化: 五层+Range+概率

旧: MALF_Definitive_v2_1-deepseek-20260726
新: MALF_v2.1_StructuralPosition_Implemented
变化: 结构位置+已实现
```

---

## 📊 演化一眼看清

```
v1.0_GraphicCore_SingleFile          (图解，最简洁)
  ↓
v1.2_ThreeLayer_Split                (分层：Core/Lifespan/Service)
  ↓
v1.3_GuardPrecision_Charts           (精确化：current_effective_guard)
  ↓
v1.4_BoundaryRules                   (边界：edge case处理)
  ↓
v1.5_BehaviorBucket                  (行为：延续/停滞描述)
  ↓
v2.0_FiveLayer_Range_Probability     (重构：五层+Range+概率)
  ↓
v2.1_StructuralPosition_Implemented  (改名+实现：Sperandeo-malf-engine)
  ↓
v3.0_CoreMinimal_BackToBasics        (回归：10概念+3功能+1层)
```

---

## 🎯 核心关键词

### 架构演化

- **SingleFile** - 单文件（v1.0）
- **ThreeLayer** - 三层（v1.2）
- **FiveLayer** - 五层（v2.0）
- **CoreMinimal** - 核心最小（v3.0）

### 功能演化

- **GraphicCore** - 图解核心（v1.0）
- **Split** - 分层（v1.2）
- **GuardPrecision** - 守护点精确（v1.3）
- **BoundaryRules** - 边界规则（v1.4）
- **BehaviorBucket** - 行为bucket（v1.5）
- **Range** - 区间层（v2.0）
- **Probability** - 概率层（v2.0）
- **StructuralPosition** - 结构位置（v2.1）

### 状态标识

- **Charts** - 加图表（v1.3）
- **Implemented** - 有实现（v2.1）
- **BackToBasics** - 回归基础（v3.0）

---

## 📁 最终目录结构

```
B:\trading-reference\malf-Definitive\
  │
  ├─ VERSION-NAMING-GUIDE.md              ← 本文件
  ├─ MALF-FINAL-MINIMAL-SPEC.md          ← 最终规格
  ├─ MALF-v3.0-CORE-MINIMAL.md           ← v3.0定义
  ├─ MALF-VERSION-EVOLUTION.md           ← 演化史
  ├─ ULTIMATE-TRUTH-GENEALOGY.md         ← 终极真相
  │
  ├─ MALF_v1.0_GraphicCore_SingleFile\   ← v1.0 图解版
  ├─ MALF_v1.2_ThreeLayer_Split\         ← v1.2 三层分离
  ├─ MALF_v1.3_GuardPrecision_Charts\    ← v1.3 守护点精确
  ├─ MALF_v1.4_BoundaryRules\            ← v1.4 边界规则
  ├─ MALF_v1.5_BehaviorBucket\           ← v1.5 行为bucket
  ├─ MALF_v2.0_FiveLayer_Range_Probability\  ← v2.0 五层重构
  ├─ MALF_v2.1_StructuralPosition_Implemented\ ← v2.1 已实现
  │
  ├─ ARCHIVED-余年-Definitive-2026-11-23\     ← 归档（余年相关）
  ├─ ARCHIVED.md                          ← 归档说明
  └─ README.md                            ← 总导航
```

---

## 🔍 快速定位

想找什么版本？看名字：

| 需求 | 版本 |
|------|------|
| **最简洁图解** | v1.0_GraphicCore |
| **分层架构开始** | v1.2_ThreeLayer |
| **守护点精确定义** | v1.3_GuardPrecision |
| **五层完整实现** | v2.1_StructuralPosition_Implemented |
| **当前权威定义** | v3.0 (单独文件，不在目录里) |

---

## 💡 未来新版本命名建议

### 格式

```
MALF_v{版本号}_{核心变化}_{次要特征}
```

### 示例

假设未来有v4.0:
```
MALF_v4.0_AdaptiveSampling_RealTime
      ↑     ↑                  ↑
      版本  核心变化          次要特征
```

### 关键词建议

**架构类**:
- Minimal, Core, Layered, Modular, Unified

**功能类**:
- Adaptive, Dynamic, Static, Incremental, Realtime

**状态类**:
- Draft, Stable, Deprecated, Implemented, Tested

---

**状态**: ✅ 重命名完成

**原则**: 看名字就知道改了什么！

