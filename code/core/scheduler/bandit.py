"""受限上下文 bandit 在线模型选择（§6.3.2 在线自适应）。

从 #4 执行反馈学习：以 (s_w, σ_w) 为上下文，arm = (层, 模型)。
- 奖励 = 质量 κ × 成功指示，最大化。
- 硬约束（packing）：累计成本 ≤ 预算 B。
- 软约束（covering）：时延违规率 ≤ ε，超阈值时偏向低时延 arm。
- UCB1 平衡探索-利用，理论上次线性 regret（§6.3.2 引 Online LLM Selection Bandits）。"""
from __future__ import annotations
import math
from dataclasses import dataclass
from collections import defaultdict
from typing import Optional
from core.scheduler.models import Subtask


@dataclass
class ArmStats:
    n: int = 0
    reward_sum: float = 0.0
    cost_sum: float = 0.0
    latency_sum: float = 0.0
    sla_violations: int = 0

    @property
    def mean_reward(self) -> float:
        return self.reward_sum / self.n if self.n > 0 else 0.0


class ContextualBandit:
    """上下文 = (计算规模, 敏感等级)；每个上下文独立维护 arm 统计。"""

    def __init__(self, c: float = 1.0, budget: float = float("inf"),
                 sla_threshold: float = 0.1):
        self.c = c                       # 探索系数
        self.budget = budget             # 硬预算（累计成本上限）
        self.spent = 0.0
        self.sla_threshold = sla_threshold
        self.stats: dict[tuple, dict[tuple[str, str], ArmStats]] = defaultdict(dict)
        self.total_n = 0

    def _context(self, w: Subtask) -> tuple:
        return (w.scale, w.sensitivity)

    def _violation_rate(self, ctx: tuple) -> float:
        arms = self.stats.get(ctx, {})
        tot = sum(s.n for s in arms.values())
        if tot == 0:
            return 0.0
        return sum(s.sla_violations for s in arms.values()) / tot

    def select(self, w: Subtask, arms: list[tuple[str, str]],
               est_cost: dict, est_lat: dict) -> Optional[tuple[str, str]]:
        """在可行 arms 中选一个；无 arm 返回 None。"""
        if not arms:
            return None
        ctx = self._context(w)
        ctx_stats = self.stats[ctx]
        # 硬预算筛选；预算耗尽则降级为全集（仅记录，不阻塞）
        affordable = [a for a in arms if self.spent + est_cost.get(a, 0.0) <= self.budget]
        candidates = affordable if affordable else arms
        viol_rate = self._violation_rate(ctx)
        log_n = math.log(max(self.total_n, 1))

        def score(a: tuple[str, str]) -> float:
            s = ctx_stats.get(a)
            if s is None or s.n == 0:
                return float("inf")  # 未探索优先
            ucb = s.mean_reward + self.c * math.sqrt(log_n / s.n)
            if viol_rate > self.sla_threshold:
                # 软 SLA 告警：惩罚高时延 arm
                ucb -= 0.5 * (est_lat.get(a, 0.0) / max(w.latency_budget_ms, 1.0))
            return ucb

        return max(candidates, key=score)

    def update(self, w: Subtask, arm: tuple[str, str],
               reward: float, cost: float, latency_ms: float) -> None:
        ctx = self._context(w)
        s = self.stats[ctx].get(arm)
        if s is None:
            s = ArmStats()
            self.stats[ctx][arm] = s
        s.n += 1
        s.reward_sum += reward
        s.cost_sum += cost
        s.latency_sum += latency_ms
        if latency_ms > w.latency_budget_ms:
            s.sla_violations += 1
        self.spent += cost
        self.total_n += 1

    def arm_distribution(self, ctx: tuple) -> dict[tuple[str, str], float]:
        """返回某上下文下各 arm 的选择占比。"""
        arms = self.stats.get(ctx, {})
        tot = sum(s.n for s in arms.values())
        if tot == 0:
            return {}
        return {a: s.n / tot for a, s in arms.items()}
