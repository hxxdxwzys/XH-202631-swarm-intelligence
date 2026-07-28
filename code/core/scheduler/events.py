"""结构化调度事件日志（§6.5 输出 → #5/#7/#8，对应赛题"推理轨迹"交付）。

每条调度决策记为一个 typed 事件，可写 JSONL 供回放、统计与可视化。
对应知识库 [[2606.04990 Agent Traces to Trust Survey]] 的 provenance 思路。"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, asdict
from collections import Counter
from core.scheduler.models import ScheduleDecision


@dataclass
class ScheduleEvent:
    step: int
    subtask_id: str
    layer: str
    model: str
    split_mode: str          # 'none' | 'layer' | 'phase'
    latency_ms: float
    cost: float
    feasible: bool
    reason: str


class ScheduleLogger:
    def __init__(self, path: str | None = None):
        self.events: list[ScheduleEvent] = []
        self.path = path

    def log(self, decision: ScheduleDecision, step: int) -> ScheduleEvent:
        ev = ScheduleEvent(
            step=step, subtask_id=decision.subtask_id,
            layer=decision.layer_name, model=decision.model_name,
            split_mode=(decision.split.mode if decision.split else "none"),
            latency_ms=round(decision.latency_ms, 1),
            cost=round(decision.cost, 4),
            feasible=decision.feasible, reason=decision.reason,
        )
        self.events.append(ev)
        return ev

    def write_jsonl(self) -> None:
        if not self.path:
            return
        d = os.path.dirname(self.path)
        if d:
            os.makedirs(d, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            for ev in self.events:
                f.write(json.dumps(asdict(ev), ensure_ascii=False) + "\n")

    def summary(self) -> dict:
        n = len(self.events)
        if n == 0:
            return {"n": 0}
        feas = [e for e in self.events if e.feasible]
        nf = len(feas)
        layers = Counter(e.layer for e in feas)
        return {
            "n": n,
            "feasible": nf,
            "infeasible": n - nf,
            "splits": sum(1 for e in feas if e.split_mode != "none"),
            "layer_dist": dict(layers),
            "avg_latency_ms": round(sum(e.latency_ms for e in feas) / max(nf, 1), 1),
            "total_cost": round(sum(e.cost for e in feas), 4),
        }
