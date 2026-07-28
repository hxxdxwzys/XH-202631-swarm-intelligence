"""两阶段自适应调度器（§6.3）。

阶段一：隐私硬筛 → 能力/显存/时延可行域 → 不可行则尝试模型切分。
阶段二：在可行域内选择 —— 基类用代价函数 J，AdaptiveScheduler 用受限 bandit。
切分：层切分（EdgeShard 式）与阶段切分（prefill/decode）择优。"""
from __future__ import annotations
from typing import Optional
from core.scheduler.models import (
    Subtask, ScheduleDecision, SplitPlan, ResourceEnvironment,
    ModelProfile, ResourceLayer, allowed_layer_kinds,
)
from core.scheduler.metrics import (
    latency_single, cost_single,
    latency_layer_split, cost_layer_split,
    latency_phase_split, cost_phase_split,
)
from core.scheduler.split import best_layer_split, best_phase_split
from core.scheduler.ports import ExecutorPort


class Scheduler:
    """端-边-云自适应调度器（规则硬约束 + 代价最优）。"""

    def __init__(self, env: ResourceEnvironment, executor: ExecutorPort,
                 weights: tuple[float, float, float] = (1.0, 0.01, 0.5)):
        """
        weights: (α, β, γ) —— 时延项、资源开销项、质量缺口项权重（§6.3.2 J）。
        """
        self.env = env
        self.executor = executor
        self.alpha, self.beta, self.gamma = weights

    def schedule(self, w: Subtask) -> ScheduleDecision:
        allowed_kinds, feasible = self._feasible(w)
        if feasible:
            layer, m, lat = self._select(w, feasible)
            return ScheduleDecision(
                subtask_id=w.id, layer_name=layer.name, model_name=m.name,
                split=None, latency_ms=lat, cost=cost_single(w, layer, m),
                feasible=True,
            )
        # 单层不可行 → 尝试模型切分
        split_decision = self._try_split(w, allowed_kinds)
        if split_decision is not None:
            return split_decision
        return ScheduleDecision(
            subtask_id=w.id, layer_name="", model_name="",
            feasible=False, reason="无可行层/模型，且不可切分（回送 #1 重规划）",
        )

    # —— 阶段一：可行域 ——
    def _feasible(self, w: Subtask) -> tuple[tuple[str, ...],
                                             list[tuple[ResourceLayer, ModelProfile, float]]]:
        """隐私硬筛 + 能力/显存/时延可行域。"""
        allowed_kinds = allowed_layer_kinds(w.sensitivity)
        allowed_layers = [l for l in self.env.layers if l.kind in allowed_kinds]
        feasible: list[tuple[ResourceLayer, ModelProfile, float]] = []
        for layer in allowed_layers:
            for m in layer.models:
                if not m.can_handle(w.scale):
                    continue
                if m.required_mem_gb > layer.mem_gb:        # 显存承载
                    continue
                if layer.compute_tps <= 0:
                    continue
                lat = latency_single(w, layer, m)
                if lat <= w.latency_budget_ms:              # 时延预算
                    feasible.append((layer, m, lat))
        return allowed_kinds, feasible

    # —— 阶段二：选择（基类=代价 J 最优；子类可覆盖为 bandit）——
    def _select(self, w: Subtask,
                feasible: list[tuple[ResourceLayer, ModelProfile, float]]
                ) -> tuple[ResourceLayer, ModelProfile, float]:
        return min(feasible, key=lambda t: self._J(w, t[0], t[1], t[2]))

    def _J(self, w: Subtask, layer: ResourceLayer, m: ModelProfile, lat: float) -> float:
        """代价函数 J = α·Lat/τ + β·Cost + γ·(1−κ)（§6.3.2）。"""
        cost = cost_single(w, layer, m)
        quality_gap = 1.0 - m.capability
        return (self.alpha * (lat / w.latency_budget_ms)
                + self.beta * cost
                + self.gamma * quality_gap)

    # —— 模型切分 ——
    def _try_split(self, w: Subtask,
                   allowed_kinds: tuple[str, ...]) -> Optional[ScheduleDecision]:
        candidate_models = [
            m for l in self.env.layers if l.kind in allowed_kinds for m in l.models
        ]
        if not candidate_models:
            return None
        model = max(candidate_models, key=lambda m: m.capability)
        if not model.can_handle(w.scale):
            return None  # 模型能力不足，切分无意义

        # 候选 1：层切分
        layer_plan = best_layer_split(w, model, self.env, allowed_kinds)
        layer_dec = None
        if layer_plan is not None:
            lat = latency_layer_split(w, layer_plan, self.env)
            if lat <= w.latency_budget_ms:
                layer_dec = (layer_plan, lat, cost_layer_split(w, layer_plan, self.env))

        # 候选 2：阶段切分
        phase_plan = best_phase_split(w, model, self.env, allowed_kinds)
        phase_dec = None
        if phase_plan is not None:
            p = self.env.by_name(phase_plan.phase_layers[0])
            d = self.env.by_name(phase_plan.phase_layers[1])
            lat = latency_phase_split(w, model, p, d)
            if lat <= w.latency_budget_ms:
                phase_dec = (phase_plan, lat, cost_phase_split(w, model, p, d))

        best = None
        for dec in (layer_dec, phase_dec):
            if dec is None:
                continue
            if best is None or dec[1] < best[1]:
                best = dec
        if best is None:
            return None
        plan, lat, cost = best
        if plan.mode == "layer":
            main_layer = max(
                plan.block_allocation,
                key=lambda nb: (self.env.by_name(nb[0]).compute_tps
                                if self.env.by_name(nb[0]) else 0.0),
            )[0]
        else:
            main_layer = plan.phase_layers[0]
        return ScheduleDecision(
            subtask_id=w.id, layer_name=main_layer, model_name=model.name,
            split=plan, latency_ms=lat, cost=cost, feasible=True,
            reason=f"{plan.mode}-split",
        )
