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


def latency_phase_split(w: Subtask, model: ModelProfile,
                        p_layer: ResourceLayer, d_layer: ResourceLayer) -> float:
    """阶段切分时延（§6.4 模式B）：prefill(计算密集)→p 层，decode(访存密集)→d 层。"""
    if p_layer.compute_tps <= 0 or d_layer.compute_tps <= 0:
        return float("inf")
    prefill_ms = w.est_input_tok / p_layer.compute_tps * 1000.0
    decode_ms = w.est_output_tok / d_layer.compute_tps * 1000.0
    kv_transfer = d_layer.rtt_ms + model.blocks * KV_PER_BLOCK_MS  # KV 从 p 传到 d
    return p_layer.rtt_ms + prefill_ms + kv_transfer + decode_ms


def cost_phase_split(w: Subtask, model: ModelProfile,
                     p_layer: ResourceLayer, d_layer: ResourceLayer) -> float:
    """阶段切分资源开销：prefill token 在 p 层计费，decode token 在 d 层计费。"""
    return ((w.est_input_tok / 1000.0) * p_layer.cost_per_1k_tok
            + (w.est_output_tok / 1000.0) * d_layer.cost_per_1k_tok)


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


# ===== v0.3 时间均衡指标 =====

def makespan(loads: dict[str, float]) -> float:
    """批量调度的 makespan：各层负载的最大值（最后完成的层）。
    定义：从首批任务启动到末批任务完成的总时长。"""
    return max(loads.values()) if loads else 0.0


def load_balance_index(loads: dict[str, float]) -> float:
    """负载均衡度（Jain 公平指数）：1 = 完全均衡，1/n = 全部集中在一层。
    定义：各层负载的公平性度量，越接近 1 说明工作分布越均匀。"""
    vals = list(loads.values())
    n = len(vals)
    if n == 0:
        return 1.0
    total = sum(vals)
    if total == 0:
        return 1.0
    return total * total / (n * sum(v * v for v in vals))


def idle_ratio(loads: dict[str, float]) -> float:
    """空闲率：各层在 makespan 内的空闲时间占比。
    定义：makespan 内所有层未在计算的空闲总时间 / (层数 × makespan)。
    越低说明资源利用越充分。"""
    vals = list(loads.values())
    n = len(vals)
    if n == 0:
        return 0.0
    m = max(vals) if vals else 0.0
    if m == 0:
        return 0.0
    total_load = sum(vals)
    total_idle = n * m - total_load
    return total_idle / (n * m)
