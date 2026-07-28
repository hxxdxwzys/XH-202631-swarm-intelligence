"""自适应调度器 —— 在规则硬约束之上，用受限 bandit 做 stage-2 在线选择（§6.3.2）。

硬约束（隐私/能力/显存/时延）仍由 Scheduler._feasible 保证；
bandit 仅在可行域内学习"哪个 arm（层,模型）回报最高"，从 #4 反馈持续自适应。"""
from __future__ import annotations
from core.scheduler.scheduler import Scheduler
from core.scheduler.bandit import ContextualBandit
from core.scheduler.models import Subtask, ScheduleDecision
from core.scheduler.metrics import cost_single
from core.scheduler.ports import ExecutionResult


class AdaptiveScheduler(Scheduler):
    def __init__(self, env, executor, bandit: ContextualBandit | None = None,
                 weights: tuple[float, float, float] = (1.0, 0.01, 0.5)):
        super().__init__(env, executor, weights)
        self.bandit = bandit or ContextualBandit()

    def _select(self, w, feasible):
        """覆盖基类：用 bandit 在可行域内选 arm；bandit 无主见时回退代价 J。"""
        arms = [(l.name, m.name) for l, m, _ in feasible]
        est_cost = {(l.name, m.name): cost_single(w, l, m) for l, m, _ in feasible}
        est_lat = {(l.name, m.name): lat for l, m, lat in feasible}
        arm = self.bandit.select(w, arms, est_cost, est_lat)
        if arm is None:
            return super()._select(w, feasible)
        for l, m, lat in feasible:
            if (l.name, m.name) == arm:
                return l, m, lat
        return super()._select(w, feasible)

    def feedback(self, w: Subtask, decision: ScheduleDecision,
                 result: ExecutionResult) -> None:
        """执行后回灌 bandit：仅对单层可行决策学习，切分决策暂不学。"""
        if not decision.feasible or decision.split is not None:
            return
        layer = self.env.by_name(decision.layer_name)
        model = layer.find_model(decision.model_name) if layer else None
        quality = model.capability if model else 0.5
        reward = quality * (1.0 if result.success else 0.0)
        self.bandit.update(w, (decision.layer_name, decision.model_name),
                           reward, result.cost, result.latency_ms)
