"""调度性能指标（§6.4）：端到端时延、资源开销、隐私约束满足率。"""
from __future__ import annotations
from core.scheduler.models import (
    ResourceLayer, ResourceEnvironment, ModelProfile, Subtask,
    ScheduleDecision, SplitPlan, allowed_layer_kinds,
)

# 每块的 KV 状态跨层传输开销系数（ms/块）
KV_PER_BLOCK_MS = 2.0


def latency_single(w: Subtask, layer: ResourceLayer, model: ModelProfile) -> float:
    """单层执行时延：δ + t_pre + t_dec（§6.4）。"""
    if layer.compute_tps <= 0:
        return float("inf")
    compute_ms = w.tokens / layer.compute_tps * 1000.0
    return layer.rtt_ms + compute_ms


def cost_single(w: Subtask, layer: ResourceLayer, model: ModelProfile) -> float:
    """单层资源开销：(tok_in+tok_out)/1000 × p_ℓ（§6.4）。"""
    return (w.tokens / 1000.0) * layer.cost_per_1k_tok


def latency_layer_split(w: Subtask, plan: SplitPlan,
                        env: ResourceEnvironment) -> float:
    """层切分时延：Σ 各层计算 + Σ 跨层 KV 传输（§6.4 模式A）。"""
    total_blocks = sum(b for _, b in plan.block_allocation) or 1
    total_compute = 0.0
    total_transfer = 0.0
    prev_name: str | None = None
    first_rtt = 0.0
    for i, (name, b) in enumerate(plan.block_allocation):
        layer = env.by_name(name)
        if layer is None or layer.compute_tps <= 0 or b <= 0:
            continue
        if i == 0:
            first_rtt = layer.rtt_ms
        # 该层承担 b 块的计算时间（按块比例折算）
        total_compute += (w.tokens * b / total_blocks) / layer.compute_tps * 1000.0
        if prev_name is not None:
            # 跨层传输：对端层 rtt + 块相关开销
            total_transfer += layer.rtt_ms + b * KV_PER_BLOCK_MS
        prev_name = name
    return first_rtt + total_compute + total_transfer


def cost_layer_split(w: Subtask, plan: SplitPlan, env: ResourceEnvironment) -> float:
    """层切分资源开销：按块比例摊到各层。"""
    total_blocks = sum(b for _, b in plan.block_allocation) or 1
    total = 0.0
    for name, b in plan.block_allocation:
        layer = env.by_name(name)
        if layer is None:
            continue
        total += (w.tokens / 1000.0) * layer.cost_per_1k_tok * (b / total_blocks)
    return total


def privacy_satisfaction(decisions: list[ScheduleDecision],
                         subtasks: list[Subtask],
                         env: ResourceEnvironment) -> float:
    """隐私约束满足率 P_priv = 1 − 违规数/总数（§6.4）。"""
    if not decisions:
        return 1.0
    sub_by_id = {s.id: s for s in subtasks}
    kinds = env.kinds_by_name()
    violations = 0
    for d in decisions:
        if not d.feasible:
            continue
        s = sub_by_id.get(d.subtask_id)
        if s is None:
            continue
        if kinds.get(d.layer_name, "") not in allowed_layer_kinds(s.sensitivity):
            violations += 1
    return 1.0 - violations / len(decisions)
