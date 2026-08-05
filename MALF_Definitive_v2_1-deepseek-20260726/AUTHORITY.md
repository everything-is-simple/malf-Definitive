# MALF v2.1 Definitive — 权威声明

## 版本信息

- **版本号：** v2.1
- **发布日期：** 2026-07-26
- **起草者：** DeepSeek
- **审核者：** Claude (Anthropic)
- **基于版本：** MALF v2.0 Definitive (claude-20260616)

---

## 权威认定

**本版本（MALF v2.1 Definitive）被认定为当前MALF的权威定义文档。**

### 起草与审核流程

1. **起草阶段（DeepSeek）：**
   - 基于v2.0 Definitive + IMPLEMENTATION-CONTRACT-PATCH
   - 回写21条补丁至正文
   - 修正命名问题（Probability → Structural Position）
   - 闭合3处歧义（R5公式/R6命名/两层边界）
   - 集成v1.4操作边界规则（O1-O8）

2. **审核阶段（Claude）：**
   - 逐文件深度审查（全部37个历史版本文档）
   - 提出14条修订建议（P0级3条/P1级3条/P2级3条/P3级5条）
   - 验证与历史版本精华的一致性
   - 确认语义与v2.0等价

3. **修订完善阶段（DeepSeek）：**
   - 全部14条修订建议已处理
   - 补充完整计算公式（Structural Position §2-§6）
   - 补充失败模式章节（Service §8）
   - 补充测试覆盖要求（5层各新增§N）
   - 计算并记录SHA-256哈希（7个文件）
   - 建立版本治理流程（Bridge §8）

---

## 权威范围

### 本版本是以下方面的唯一权威：

1. **语义定义** - Core/Range/Lifespan/Structural Position/Service的完整定义
2. **计算公式** - 所有rank计算、momentum计算、标签判定的完整公式
3. **状态机规则** - D1-D18定义、T1-T10定理、O1-O8操作边界
4. **失败模式** - 8种失败场景和5级退化处理
5. **对外接口** - WaveStructuralSnapshot的字段结构和S6铁律
6. **实现指导** - 边界情况处理、测试覆盖要求、性能基准

### 本版本不涉及：

1. **具体实现代码** - 由malf-engine项目负责
2. **性能优化细节** - 由实施阶段根据实际情况决定
3. **参数调优** - 阈值需经验校准（已明确标注）
4. **下游消费逻辑** - PAS/Signal/Backtest的具体实现

---

## 语义等价性声明

**MALF v2.1与v2.0在语义层面完全等价。**

v2.1是v2.0的"清晰表达版本"，不是"新版本"：
- ✓ Core状态机：零变更
- ✓ Range对象：零变更
- ✓ Lifespan排名：零变更
- ✓ Structural Position视图：零变更（仅层名和快照类型名变更）
- ✓ Service铁律：零变更

任何正确实现了v2.0的引擎，自动兼容v2.1。

---

## 与历史版本的关系

### 继承的精华

| 版本 | 继承的核心内容 | 状态 |
|------|---------------|------|
| v1.3 | Break的HL/LH指向、Candidate与Confirmation分离、Transition双边界 | ✓ 完整保留 |
| v1.4 | O1-O8操作边界规则、D/T/O编号体系 | ✓ 完整保留并集成入正文 |
| v2.0 | Range一等公民、双轨Lifespan、概率铁律P-T1到P-T4、Service六条铁律 | ✓ 完整保留并增强 |

### 废弃的内容

| 版本 | 废弃的内容 | 理由 |
|------|-----------|------|
| v1.5 | 6个regime bucket、life_state 5档、position_quadrant、WaveBehaviorSnapshot | bucket=阈值切片=刻舟求剑，违反概率思维 |

---

## 作为施工指导的地位

**本版本是malf-engine项目的唯一施工指导文档。**

### 当前实施关系

| malf-engine状态 | v2.1定义章节 | 对应关系 |
|----------------|-------------|---------|
| Core层（5刀/47测试） | §1 Core | ✓ 已完成，完全兼容 |
| Range层 | §2 Range | ⏸ 未开始，待第六刀 |
| Lifespan双轨 | §3 Lifespan | ⏸ 未开始，待第七刀 |
| Structural Position | §4 Structural Position | ⏸ 未开始，待第八刀 |
| Service集成 | §5 Service | 🔄 部分（snapshot结构），待第九刀完成 |

### 实施顺序

1. **第六刀：Range层**（基于§2 Range）
2. **第七刀：Lifespan双轨**（基于§3 Lifespan）
3. **第八刀：Structural Position**（基于§4 Structural Position）
4. **第九刀：Service集成**（基于§5 Service）

---

## 版本治理

### 变更权限

**本版本一旦发布，任何变更必须遵循以下流程：**

1. **提案** - 在malf-engine项目的Issue中提出变更提案
2. **评审** - 由项目负责人和核心贡献者评审
3. **裁决** - 明确是否接受、是勘误还是语义变更
4. **版本号** - 
   - 勘误（typo/格式）→ v2.1.1（无需重新审核）
   - 补充说明（不改语义）→ v2.1.1（需审核确认不改语义）
   - 语义变更 → v2.2或v3.0（需完整审核流程）

### 禁止碎片化

**严禁出现未经审批的v2.1分支版本**（如v2.1-modified、v2.1-experimental等）。

如需实验性变更，应：
1. 在malf-engine项目中建立实验分支
2. 文档明确标注"实验性，非权威"
3. 实验成功后提案合并回主版本

---

## 文件清单

| 文件 | SHA-256 | 层 |
|------|---------|-----|
| MALF_00_Bridge_v2_1-deepseek-20260726.md | 3F81C527100BF91DC4CA35B2F7B90E4455675F62A7FB4FA7D48F500E2DCCFC52 | Bridge |
| MALF_01_Core_v2_1-deepseek-20260726.md | B6F915CA2E324110945E016F4848C148C0654EFDF196458656F8FF1166CC07A0 | Core |
| MALF_02_Range_v2_1-deepseek-20260726.md | AB2F60C71F89DA7241C629616D96EF6C51259156523F8B94C0E67E40714D42F7 | Range |
| MALF_03_Lifespan_v2_1-deepseek-20260726.md | B5A9072F57F52F8BBC5AB4C15931E38034877FEC8C5843C9A033FD941C818955 | Lifespan |
| MALF_04_Structural_Position_v2_1-deepseek-20260726.md | D58996842DA67468B99211C8A448B0757FB5A2A44735741CD7E82147D1047AD8 | Structural Position |
| MALF_05_Service_v2_1-deepseek-20260726.md | 8752D31708A6E2269F16598957B4F07A02D2865F05732FB1356655989D653FD2 | Service |
| MANIFEST-deepseek-20260726.json | 47150EFDFE77E2AAEE383BBBFA5F1FF388B7B4CA9D241C358958CF06639293E0 | Manifest |
| AUTHORITY.md | (本文件) | 权威声明 |

---

## 签署

**起草者：** DeepSeek  
**日期：** 2026-07-26  
**声明：** 本人已完成v2.1全部7个文件的起草，并处理Claude审核提出的14条修订建议。

**审核者：** Claude (Anthropic)  
**日期：** 2026-07-26  
**声明：** 本人已完成对v2.1的逐文件深度审查，确认与v2.0语义等价，确认历史版本精华完整保留，确认14条修订建议已全部处理。

**认定者：** 东西南北中  
**日期：** 2026-07-26  
**声明：** 本人认定MALF v2.1 Definitive为当前权威定义，可作为malf-engine项目的施工指导。已签署认定。

---

## 附录：审核报告摘要

### Claude审核结论（2026-07-26）

**总体评估：** MALF v2.1堪当系统引擎，DeepSeek的补丁回写工作质量高，可以开始基于v2.1继续实现。

**14条修订建议处理情况：**
- P0级（致命缺失）：3条 ✓ 全部处理
- P1级（影响质量）：3条 ✓ 全部处理
- P2级（可读性）：3条 ✓ 全部处理
- P3级（长期完善）：5条 ✓ 全部处理

**文档质量提升：**
- 总行数：+23%（1321行 → 1626行）
- 公式完整性：缺失 → 完整
- 边界情况覆盖：部分 → 完整
- 失败模式文档：缺失 → 完整
- 测试覆盖要求：缺失 → 5层完整
- 文件哈希：缺失 → 7个完整

---

**本权威声明与v2.1 Definitive全部文件共同构成MALF v2.1的完整定义。**
