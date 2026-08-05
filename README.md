# malf-Definitive — MALF 权威定义全集（v1.0–v2.1）

> **远端仓库**: https://github.com/everything-is-simple/malf-Definitive
> **本地镜像**: `Z:\ai-malf-riskbench-Definitive\malf-Definitive（v1.0-v2.1）`
> **只读性质**: 本仓库是 MALF 领域权威定义的历史与现行全集，**只读**；任何修改须走版本治理流程（Bridge §8）。

## 目录结构（7 个版本）

| 目录 | 版本 | 定位 | 文件 |
|------|------|------|------|
| `MALF_Three_Part_Design_Set_v1_0` | v1.0 | 梦开始的地方：波段标尺四图版（PDF）+ 图示化重生成 | 5 |
| `MALF_Three_Part_Design_Set_v1_2` | v1.2/1.3 过渡 | 三文档结构（Bridge + Core v1.3 定稿 + Lifespan + Service） | 4 |
| `MALF_Three_Part_Design_Set_v1_3` | v1.3 | 双边界模型诞生版（三件套 + 3 Chart View + Review） | 15 |
| `MALF_Three_Part_Design_Set_v1_4` | v1.4 | O1-O8 操作边界（v2.1 §9 直接来源） | 10 |
| `MALF_Three_Part_Design_Set_v1_5` | v1.5 | wave_behavior_snapshot（v2.0/v2.1 正式废弃） | 10 |
| `MALF_Definitive_v2_0-claude-20260616` | v2.0 | Probability 层、Range 一等公民、双轨 Lifespan | 7 |
| `MALF_Definitive_v2_1-deepseek-20260726` | **v2.1（现行权威）** | 当前唯一权威；与 v2.0 语义等价（结构层） | 8 |

## 权威链

1. **v2.1 Definitive**（`MALF_Definitive_v2_1-deepseek-20260726/`）= 领域语义最高权威；SHA-256 固定于主仓 `docs/02-权威来源登记.md`
2. v2.0 = v2.1 语义等价基准（Probability → Structural Position 命名 + 补丁回写）
3. v1.4 = O1-O8 操作边界来源；v1.3 = 双边界模型来源；v1.5 = 废弃内容记录（6 regime/life_state/quadrant/WaveBehaviorSnapshot）
4. v1.0-v1.2 = 演进早期（波段标尺/三文档）；对齐关系见主仓 `docs/03/04/05` 矩阵

## 版本演进验证（主仓 T9 系列，2026-08-05）

```
v1.0 → v1.2 → v1.3 → v1.4 → v1.5 → v2.0 → v2.1
 ✅     ✅     ✅     ✅     ✅     ✅核对  权威
```

- T9.1：v1.0 → v2.1 对齐（33 条承接 + 5 裁决点进化淘汰）
- T9.2：v1.0 图示化重生成
- T9.3：v1.2 vs v2.1 对比（F1/F2/F3 裁决）
- T9.4-T9.7：v1.2/v1.3/v1.4/v1.5 按 v2.1 修订版
- T9.8：v2.0 vs v2.1 语义等价核对（H1-H5 裁决）

## 与本仓库的关系

- 主仓 `github.com/everything-is-simple/ai-malf-riskbench`（AI MALF RiskBench 工程仓）通过 AGENTS.md §3/§4 引用本仓库为只读权威源
- 本仓库不包含任何代码实现、数据库或运行产物；仅语义与历史定义

---

**登记**: 2026-08-05（用户建立集中权威目录 + 新建远端库；T9 系列授权初始化与推送）
