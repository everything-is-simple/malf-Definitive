# MALF v1.5 Lifespan Stats Definitions and Theorems

日期：2026-05-16

## 1. Lifespan 侧新增对象

### 定义 L1：`stagnation_regime`

`stagnation_regime` 描述当前 wave 的停滞压力：

```text
fresh
watchful
stalled
terminal_pressure
```

它来自 `no_new_span / stagnation_rank / life_state`。

### 定义 L2：`transition_regime`

`transition_regime` 描述当前 transition 的行为：

```text
clean_handoff
replacement_heavy
prolonged_unresolved
not_applicable
```

它来自 `transition_span / candidate_replacement_count / open_transition_id`。

### 定义 L3：`birth_quality_regime`

`birth_quality_regime` 描述当前 wave 的出生代价：

```text
clean_birth
negotiated_birth
costly_birth
unknown_birth
```

它来自 `candidate_wait_span / candidate_replacement_count / confirmation_distance_abs / confirmation_distance_pct`。

## 2. Lifespan 定理

1. `transition_span` 仍不并入 `no_new_span`。
2. 出生质量只描述形成过程，不描述未来收益。
3. `replacement_heavy` 只说明 transition 摇摆，不说明多空优劣。
4. 生命周期统计仍然服务于结构行为事实，而不是 alpha 证明。
