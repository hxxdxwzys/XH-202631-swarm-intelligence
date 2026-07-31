"""时间均衡调度（v0.3）— 负载感知、批量 makespan 优化、关键路径识别。

从"逐任务最优"升级到"系统级时间均衡"：
- LoadTracker：追踪各层负载，支撑负载感知决策
- BatchScheduler：LPT 策略最小化批量并行任务的 makespan
- critical_path：DAG 关键路径识别，关键任务优先用快模型
对应赛题"性能效率 / token与时间效率"。"""
from __future__ import annotations
from typing import Callable
from core.scheduler.models import (
    Subtask, ScheduleDecision, ResourceEnvironment,
    ResourceLayer, ModelProfile,
)
from core.scheduler.scheduler import Scheduler
from core.scheduler.metrics import cost_single
from core.scheduler.ports import ExecutorPort


class LoadTracker:
    """追踪各层当前负载（累计预估时延，ms）。"""

    def __init__(self, layer_names: list[str]):
        self._load: dict[str, float] = {n: 0.0 for n in layer_names}

    def assign(self, layer_name: str, latency: float) -> None:
        """子任务派到该层，累加其预估时延。"""
        self._load[layer_name] = self._load.get(layer_name, 0.0) + latency

    def finish(self, layer_name: str, latency: float) -> None:
        """子任务完成，释放该层负载。"""
        self._load[layer_name] = max(0.0, self._load.get(layer_name, 0.0) - latency)

    def load_of(self, layer_name: str) -> float:
        return self._load.get(layer_name, 0.0)

    def earliest_finish(self, layer_name: str) -> float:
        """该层最早能开始新任务的时间（=当前累计负载）。"""
        return self._load.get(layer_name, 0.0)

    def reset(self) -> None:
        for k in self._load:
            self._load[k] = 0.0

    def loads(self) -> dict[str, float]:
        return dict(self._load)


class BatchScheduler(Scheduler):
    """批量调度器：LPT 策略最小化并行子任务批的 makespan。

    LPT（Longest Processing Time first）：
    1. 按预估时延降序排列子任务（重任务先派）
    2. 每个子任务派到"可行层中最早能完成"的层
    3. 派完后更新该层负载
    隐私/能力/显存/时延硬约束仍由 _feasible 保证。
    """

    def __init__(self, env: ResourceEnvironment, executor: ExecutorPort,
                 tracker: LoadTracker | None = None,
                 weights: tuple[float, float, float] = (1.0, 0.01, 0.5)):
        super().__init__(env, executor, weights)
        self.tracker = tracker or LoadTracker([l.name for l in env.layers])

    def schedule_batch(self, subtasks: list[Subtask]) -> list[ScheduleDecision]:
        """批量调度并行子任务，最小化 makespan。"""
        self.tracker.reset()

        # 预估每个子任务的最小时延，用于 LPT 排序
        items: list[tuple[Subtask, float, tuple[str, ...],
                          list[tuple[ResourceLayer, ModelProfile, float]]]] = []
        for w in subtasks:
            allowed_kinds, feasible = self._feasible(w)
            if feasible:
                min_lat = min(lat for _, _, lat in feasible)
                items.append((w, min_lat, allowed_kinds, feasible))
            else:
                items.append((w, float("inf"), allowed_kinds, []))

        # LPT：按时延降序（重任务先派）
        items.sort(key=lambda x: x[1], reverse=True)

        decisions: list[ScheduleDecision] = []
        for w, _, allowed_kinds, feasible in items:
            if not feasible:
                # 单层不可行 → 尝试切分
                split_dec = self._try_split(w, allowed_kinds)
                if split_dec is not None:
                    self.tracker.assign(split_dec.layer_name, split_dec.latency_ms)
                    decisions.append(split_dec)
                else:
                    decisions.append(ScheduleDecision(
                        w.id, "", "", feasible=False,
                        reason="无可行层/模型，且不可切分（回送 #1 重规划）"))
                continue

            # LPT 核心：选可行层中"当前负载 + 任务时延"最小的
            def adjusted(t: tuple[ResourceLayer, ModelProfile, float]) -> float:
                layer, _, lat = t
                return self.tracker.earliest_finish(layer.name) + lat

            layer, model, lat = min(feasible, key=adjusted)
            self.tracker.assign(layer.name, lat)
            decisions.append(ScheduleDecision(
                w.id, layer.name, model.name, None, lat,
                cost_single(w, layer, model), True,
            ))
        return decisions


def critical_path(subtasks: list[Subtask],
                  latency_fn: Callable[[Subtask], float]) -> set[str]:
    """识别 DAG 关键路径（最长加权路径上的节点 ID 集合）。

    latency_fn(w) -> 该子任务的预估时延。
    关键路径上的任务决定端到端时延，应优先用快模型；
    非关键路径任务有松弛时间，可用高质量模型。
    """
    by_id = {w.id: w for w in subtasks}
    if not by_id:
        return set()

    # 拓扑排序（DFS）
    visited: set[str] = set()
    order: list[Subtask] = []

    def visit(w: Subtask) -> None:
        if w.id in visited:
            return
        for dep in w.depends_on:
            if dep in by_id:
                visit(by_id[dep])
        visited.add(w.id)
        order.append(w)

    for w in subtasks:
        visit(w)

    # 最早完成时间 DP：ef[w] = max(ef[pred]) + latency(w)
    ef: dict[str, float] = {}
    for w in order:
        pred_ef = max((ef[d] for d in w.depends_on if d in ef), default=0.0)
        ef[w.id] = pred_ef + latency_fn(w)

    if not ef:
        return set()

    # 回溯关键路径：从最晚完成的节点沿前驱追溯
    critical: set[str] = set()
    current = max(ef, key=ef.get)
    while current:
        critical.add(current)
        w = by_id[current]
        preds = [d for d in w.depends_on if d in ef]
        if not preds:
            break
        current = max(preds, key=lambda d: ef[d])
    return critical
