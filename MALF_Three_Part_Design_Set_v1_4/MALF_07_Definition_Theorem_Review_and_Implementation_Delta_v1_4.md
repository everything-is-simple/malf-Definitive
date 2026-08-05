# MALF v1.3 定义、定理评审与实现差异表

> v1.4 baseline note: 本文件从 v1.3 继承语义基线；文件内部的 v1.3 表述表示被继承的语义内容。v1.4 的规范增量以 MALF_01B_Core_Operational_Boundary_Rules_v1_4.md 为准。

> 本文件是 `MALF_Three_Part_Design_Set_v1_3` 的评审附录。  
> 它回答两个问题：v1.3 的定义是否清晰、定理是否自洽；以及后续代码要补哪些差异。  
> 本文件不声明当前 `H:\Asteria` 代码已经实现 v1.3。

---

## 1. 总结结论

MALF v1.3 的定义主线已经清晰，定理在当前语义体系内自洽。

一句话：

```text
MALF v1.3 可以作为下一轮 repo 文档同步和代码修订的权威语义依据；
但当前实现仍只能按已通过的 MALF complete alignment closeout 口径来认定。
```

## 2. 清晰性评审

| 主题 | v1.3 裁决 | 清晰性结论 |
|---|---|---|
| Break 的 HL / LH 指向 | 使用 `current_effective_HL` / `current_effective_LH` | 清晰。它指 active wave 内最新确认且仍有效的 guard，不是任意历史 HL / LH |
| Break 后旧 wave | 旧 wave 立即 `terminated`，不得复活 | 清晰。旧 wave 只保留审计事实，不参与新生命 |
| Transition | 旧 wave terminated 后、新 wave confirmed 前的 `system_state` | 清晰。Transition 不是 wave，也不是旧 wave 延续 |
| Transition Boundary | 使用 `transition_boundary_high` / `transition_boundary_low` 双边界 | 清晰。same-direction 与 opposite-direction new wave 都有明确 reference |
| Candidate Guard | new wave 出生前的候选守护极值 | 清晰。Candidate guard 不是 wave |
| Progress Confirmation | active candidate guard 之后的方向性推进确认 | 清晰。只有突破相应 boundary 后才能确认 new wave |
| New Wave | active candidate guard + progress confirmation 双条件确认 | 清晰。删除了 `candidate confirmed` 这类混词 |
| Lifespan | 只统计 confirmed wave 的推进、停滞、rank、出生描述 | 清晰。Transition span 不并入新 wave 的 no-new-span |
| Service | 只读发布 WavePosition | 清晰。MALF 不输出 buy / sell / weight / order，也不接受下游写回 |

## 3. 定理自洽性评审

| 定理组 | 评审结论 | 说明 |
|---|---|---|
| 旧波不可复活 | 自洽 | `terminated(wave) => never alive again` 与 Break 定义一致 |
| Candidate 最新有效 | 自洽 | active candidate 由最新 candidate guard 决定，旧 candidate 可被相反方向 guard 替代 |
| 新波双条件确认 | 自洽 | candidate guard 只给候选资格，progress confirmation 才给出生事实 |
| Break 后新波创建 | 自洽 | Break 后任何已确认新结构都创建 new wave，不延伸 old wave |
| Transition 非波段 | 自洽 | Transition 是系统未决区，不产生 wave_core_state |
| Lifespan 统计定理 | 自洽 | new_count 只数 progress primitive；no_new_span 只属于 confirmed wave |
| Service 只读定理 | 自洽 | WavePosition 是结构位置接口，不是交易动作接口 |

## 4. 与当前实现的差异

当前 `H:\Asteria` 已通过的 MALF evidence 证明的是 day dense complete alignment closeout，
不是 v1.3 新增语义的完整实现。

| 层 | v1.3 新增或强化要求 | 当前后续修订方向 |
|---|---|---|
| Core | `current_effective_HL` / `current_effective_LH` 必须显式追踪 | 检查 Core ledger 是否有足够字段表达 broken guard 与当前有效 guard |
| Core | transition 双边界：`transition_boundary_high` / `transition_boundary_low` | 扩展 transition ledger、schema、builder、audit |
| Core | candidate guard 与 progress confirmation 分离 | 删除实现和文档中的 `candidate confirmed` 混词，明确 new wave confirmation |
| Core | candidate replacement count 需要可追溯 | candidate ledger 需表达 active/invalidated 或可重建替换历史 |
| Lifespan | birth descriptors：`birth_type`、`candidate_wait_span`、`candidate_replacement_count`、`confirmation_distance_abs`、`confirmation_distance_pct` | 扩展 lifespan snapshot / service publish 字段 |
| Lifespan | transition span 不并入 new wave no-new-span | 保持当前 closeout 规则，并加 v1.3 回归测试 |
| Service | WavePosition 发布 transition boundary、active candidate、confirmation pivot、新 wave id | 扩展 Service schema 与 interface audit |
| Runner | build runner 不接受 `audit-only` 写业务表；`segmented` 必须有 segmented scope | 修复 runner mode enforcement，并补契约测试 |
| Governance | `governance/module_api_contracts/malf.toml` 元数据需从旧 bounded proof 指向当前 closeout / v1.3 同步卡 | 修正 release evidence 指向与 advertised modes |
| Tests | v1.3 新字段、新审计、新 runner mode gap 需要覆盖 | 新增 MALF unit tests 与 governance check |

## 5. 不改变的边界

| 边界 | 裁决 |
|---|---|
| 是否输出交易信号 | 否 |
| 是否输出买卖、仓位、订单 | 否 |
| 是否允许 Alpha / Signal / Position 写回 MALF | 否 |
| 是否把 `wave_core_state` 与 `system_state` 合并 | 否 |
| 是否自动打开 Alpha / Signal / Position full build | 否 |
| 是否声明现有代码已经实现 v1.3 | 否 |

## 6. 后续建议卡

建议后续 repo 卡命名：

```text
malf-v1-3-authority-sync-code-revision-20260501-01
```

建议卡目标：

```text
同步 v1.3 权威定义到 repo MALF 六件套、schema、runner contract、audit spec；
修订 Core / Lifespan / Service / audit / tests；
重新形成 MALF v1.3 alignment evidence。
```

在该卡通过前，当前工程事实仍以 `malf-complete-alignment-closeout-20260430-01`
为已通过证据。

