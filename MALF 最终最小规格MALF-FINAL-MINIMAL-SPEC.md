# MALF 最终最小规格

**版本**: Final Minimal  
**创建日期**: 2026-11-23  
**状态**: 🔒 **终极定义 - 交易生命体描述**

---

## 🎯 一句话

**MALF描述交易生命体：用极值与回摆构造结构，用结构破坏定义状态转移，用推进与停滞刻画生命节奏。**

---

## 📐 Core层：描述交易生命

### 需要：10概念 + 3功能 + 1层

#### 10个核心概念

**7个原语**:
1. HH (Higher High) - 更高高点
2. HL (Higher Low) - 更高低点
3. LL (Lower Low) - 更低低点
4. LH (Lower High) - 更低高点
5. break - 结构破坏
6. new-count - 新值计数（生长）
7. no-new-span - 未创新值跨度（停滞）

**3个状态**:
8. alive - 活着
9. broken - 终止
10. reborn - 重生

#### 3个功能

**功能1: 推进×守护机制**
```
上升: HH推进 + HL守护 → break(HL)触发终止
下降: LL推进 + LH守护 → break(LH)触发终止
```

**功能2: 寿命呼吸**
```
推进期: HH/LL出现 → new-count+1, no-new-span=0
停滞期: 无新高/低 → new-count不变, no-new-span+1
波段 = 推进与停滞交替
```

**功能3: 状态转移**
```
alive → broken (守护点被破)
broken → reborn (新方向首个极值)
reborn → alive (新方向延续)
```

#### 1层架构

```
price bars → 极值识别 → HH/HL/LL/LH → 状态机 → WavePosition
```

#### 输出

```python
@dataclass
class WavePosition:
    direction: Literal["UP", "DOWN"]
    new_count: int
    no_new_span: int
    life_state: Literal["alive", "broken", "reborn"]
```

**这就足够描述交易生命体了！** ✅

---

## 📊 Lifespan层：加入历史统计（可选）

### 额外需要：+2概念 + 2功能 + 1层

#### +2个概念

11. `update_rank` - 更新次数在历史中的分位 [0, 1)
12. `stagnation_rank` - 停滞长度在历史中的分位 [0, 1)

#### +2个功能

**功能4: 样本池管理**
```python
# 三维不混
pool_key = (symbol, timeframe, direction)

# 只收已终止走势
if life_state == "broken":
    历史池[pool_key].add({
        new_count: 终止时的值,
        no_new_span: 终止时的值
    })
```

**功能5: 分位计算**
```python
# 严格小于
update_rank = count(历史i.new_count < 当前new_count) / N
stagnation_rank = count(历史i.no_new_span < 当前no_new_span) / N

# 样本门槛
if N < 30:
    update_rank = None
    stagnation_rank = None
```

#### +1层架构

```
Core层 → 历史样本池 → 分位计算 → 历史位置
```

#### 增强输出

```python
@dataclass
class WavePosition:
    # Core层（必需）
    direction: Literal["UP", "DOWN"]
    new_count: int
    no_new_span: int
    life_state: Literal["alive", "broken", "reborn"]
    
    # Lifespan层（可选）
    update_rank: float | None = None      # 历史位置
    stagnation_rank: float | None = None  # 历史位置
```

---

## 📋 配置总结

### 配置A: Core Only（最小）

**用途**: 纯结构识别，不需要历史统计

| 维度 | 数量 |
|------|------|
| 概念 | 10个 |
| 功能 | 3个 |
| 层级 | 1层 |
| 输出字段 | 4个 |

**代码量**: ~200行  
**复杂度**: 极简  
**适用**: 实时监控、信号识别

### 配置B: Core + Lifespan（标准）

**用途**: 结构识别 + 历史位置定位

| 维度 | 数量 |
|------|------|
| 概念 | 12个 (+2) |
| 功能 | 5个 (+2) |
| 层级 | 2层 (+1) |
| 输出字段 | 6个 (+2) |

**代码量**: ~500行  
**复杂度**: 中等  
**适用**: 量化回测、策略评估

### 配置C: Full Stack（完整）

**用途**: v2.1的五层实现

| 维度 | 数量 |
|------|------|
| 概念 | 20+ |
| 功能 | 10+ |
| 层级 | 5层 |
| 输出字段 | 20+ |

**代码量**: ~5000行  
**复杂度**: 高  
**适用**: 生产系统、完整平台  
**参考**: Sperandeo-malf-engine (112 passed)

---

## 🎯 推荐

### 对于arc-pinbar

**当前**: 只有Pinbar信号识别

**可选集成**:

**方案1: Core Only** ✅ **推荐**
- 加入MALF Core识别市场结构
- 替代简单的MA60
- Pinbar信号 × MALF WavePosition
- **工作量**: 1周
- **增加复杂度**: 低

**方案2: Core + Lifespan** ⚠️
- 加入历史位置统计
- 信号质量 × 历史位置
- **工作量**: 2-3周
- **增加复杂度**: 中

**方案3: 保持现状** ✅
- Phase 4.1已完成
- 收益率+154%是真实的
- 先用起来看效果
- **工作量**: 0

---

## 🗂️ 文件结构（清理后）

```
B:\trading-reference\
  │
  ├─ malf-Definitive\                    ← MALF框架定义
  │   ├─ MALF-v3.0-CORE-MINIMAL.md      ← v3.0核心定义
  │   ├─ MALF-VERSION-EVOLUTION.md      ← 演化史
  │   ├─ MALF-FINAL-MINIMAL-SPEC.md     ← 本文件（最终规格）
  │   ├─ ULTIMATE-TRUTH-GENEALOGY.md    ← 终极真相
  │   │
  │   ├─ MALF_Three_Part_Design_Set_v1_0\  ← v1.0图解版
  │   ├─ MALF_Three_Part_Design_Set_v1_2\
  │   ├─ MALF_Three_Part_Design_Set_v1_3\
  │   ├─ MALF_Three_Part_Design_Set_v1_4\
  │   ├─ MALF_Three_Part_Design_Set_v1_5\
  │   ├─ MALF_Definitive_v2_0-claude-20260616\
  │   ├─ MALF_Definitive_v2_1-deepseek-20260726\
  │   │
  │   └─ ARCHIVED-余年-Definitive-2026-11-23\  ← 已归档（余年相关）
  │
  ├─ Sperandeo-malf-engine-未完终结\      ← MALF v2.1实现
  │
  ├─ Darvas-box-trading-未完终结\         ← 余年框架定义
  │   └─ docs\66-lifespan-framework.md   (余年唯一权威)
  │
  └─ 2011-usa-斯波朗迪-专业投机原理\     ← 原书（余年来源）
```

---

## 📚 权威链

| 文档 | 用途 | 状态 |
|------|------|------|
| **本文件** | 最终最小规格 | 🔒 权威 |
| MALF-v3.0-CORE-MINIMAL.md | 详细定义 | ✅ 参考 |
| MALF v1.0图解版 | 视觉化 | ✅ 参考 |
| MALF-VERSION-EVOLUTION.md | 演化史 | 📚 历史 |
| ULTIMATE-TRUTH-GENEALOGY.md | 真相澄清 | 📚 历史 |
| Sperandeo-malf-engine | v2.1实现 | 🔧 技术 |

---

## 💡 核心结论

### 描述交易生命体

**只需要**:
- 10概念 (7原语+3状态) ✅
- 3功能 (推进守护+寿命呼吸+状态转移) ✅
- 1层 (Core) ✅

**输出**: `WavePosition(direction, new_count, no_new_span, life_state)`

**这就够了！** 🎉

### 加入历史统计

**额外需要**:
- +2概念 (update_rank, stagnation_rank)
- +2功能 (样本池管理, 分位计算)
- +1层 (Lifespan)

**可选，不是必需！**

---

**状态**: 🔒 **最终规格完成**

**清理**: ✅ 余年-Definitive已归档

**下一步**: 基于此规格实现或整合

