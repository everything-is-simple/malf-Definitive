# MALF v1.5 三文档桥接

日期：2026-05-16

## 1. 本次升级只做什么

v1.5 不改写 `MALF v1.4` 的 wave、transition、boundary、WavePosition 主定义。

v1.5 只新增一层 successor design surface：

```text
wave_behavior_snapshot
```

它的作用是把 v1.4 已有的结构事实整理成下游可审计、可消费、但仍非决策性的行为事实。

## 2. 三层桥接

```text
MALF-Core facts
+ MALF-Lifespan facts
+ MALF-Service lineage
= wave_behavior_snapshot
```

换句话说：

- Core 负责结构状态与边界。
- Lifespan 负责推进、停滞、transition 等统计位置。
- Service 负责把这些事实只读发布成快照。

## 3. 为什么需要 v1.5

PAS v1.1 已固定自己的边界：不能回头读 `PriceBar`，也不能自己重算 MALF 结构。

因此缺失的一层必须由 MALF 自己提供，但只能提供：

- 行为 bucket
- 审计理由
- lineage

不能提供：

- 强弱最终结论
- setup family
- accept / reject
- 交易动作

## 4. 本包文件职责

| 文件 | 作用 |
|---|---|
| `MALF_01` | Core 侧行为面定义 |
| `MALF_01B` | 派生顺序、比较规则、禁止越界 |
| `MALF_02` | Lifespan 侧行为面与出生质量定义 |
| `MALF_03` | Service 只读接口 |
| `MALF_04~06` | 图示说明 |
| `MALF_07` | 差异与实现面总结 |

## 5. 权威边界

```text
MALF v1.4 = immutable anchor
MALF v1.5 = successor behavior-fact package
PAS v1.2 = future consumer only
```

本包不是 runtime 证明，不是 DB schema，不是交易授权。
