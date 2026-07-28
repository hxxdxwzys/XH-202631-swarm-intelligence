"""两阶段自适应调度器（§6.3）。

阶段一：隐私硬筛 → 能力/显存/时延可行域 → 不可行则尝试模型切分。
阶段二：在可行域内按代价函数 J 最优选择。
在线自适应（受限 bandit）留 v0.2。"""
from __future__ import annotations
from typing import Optional
from core.scheduler.models import (
    Subtask, ScheduleDecision, SplitPlan, ResourceEnvironment,
    ModelProfile, ResourceLayer, allowed_layer_kinds,
)
from core.scheduler.metrics import (
    latency_single, cost_single, latency_layer_split, cost_layer_split,
)
from core.scheduler.split import best_layer_split
from core.scheduler.ports import ExecutorPort


class Scheduler:
    """端-边-云自适应调度器。"""

    def __init__(self, env: ResourceEnvironment, executor: ExecutorPort,
                 weights: tuple[float, float, float] = (1.0, 0.01, 0.5)):
        """
        weights: (α, β, γ) —— 时延项、资源开销项、质量缺口项权重（§6.3.2 J）。
        """
        self.env = env
        self.executor = executor
        self.alpha, self.beta, self.gamma = weights

    def schedule(self, w: Subtask) -> ScheduleDecision:
        # —— 阶段一：可行域筛选 ——
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

        if feasible:
            # —— 阶段二：代价最优 ——
            best = min(feasible, key=lambda t: self._J(w, t[0], t[1], t[2]))
            layer, m, lat = best
            return ScheduleDecision(
                subtask_id=w.id, layer_name=layer.name, model_name=m.name,
                split=None, latency_ms=lat, cost=cost_single(w, layer, m),
                feasible=True,
            )

        # —— 单层不可行 → 尝试模型切分 ——
        split_decision = self._try_split(w, allowed_kinds)
        if split_decision is not None:
            return split_decision

        return ScheduleDecision(
            subtask_id=w.id, layer_name="", model_name="",
            feasible=False, reason="无可行层/模型，且不可切分（回送 #1 重规划）",
        )

    def _J(self, w: Subtask, layer: ResourceLayer, m: ModelProfile, lat: float) -> float:
        """代价函数 J = α·Lat/τ + β·Cost + γ·(1−κ)（§6.3.2）。"""
        cost = cost_single(w, layer, m)
        quality_gap = 1.0 - m.capability
        return (self.alpha * (lat / w.latency_budget_ms)
                + self.beta * cost
                + self.gamma * quality_gap)

    def _try_split(self, w: Subtask,
                   allowed_kinds: tuple[str, ...]) -> Optional[ScheduleDecision]:
        # 选允许层中能力最强的模型作为切分对象
        candidate_models = [
            m for l in self.env.layers if l.kind in allowed_kinds for m in l.models
        ]
        if not candidate_models:
            return None
        model = max(candidate_models, key=lambda m: m.capability)
        if not model.can_handle(w.scale):
            return None  # 模型本身能力不足，切分无意义
        plan = best_layer_split(w, model, self.env, allowed_kinds)
        if plan is None:
            return None
        lat = latency_layer_split(w, plan, self.env)
        cost = cost_layer_split(w, plan, self.env)
        if lat > w.latency_budget_ms:
            return None
        # 主承载层 = 参与层中算力最大者
        main_layer = max(
            plan.block_allocation,
            key=lambda nb: (self.env.by_name(nb[0]).compute_tps
                            if self.env.by_name(nb[0]) else 0.0),
        )[0]
        return ScheduleDecision(
            subtask_id=w.id, layer_name=main_layer, model_name=model.name,
            split=plan, latency_ms=lat, cost=cost, feasible=True,
            reason="layer-split",
        )
