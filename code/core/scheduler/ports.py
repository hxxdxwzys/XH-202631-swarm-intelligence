"""与其它模块的抽象接口（§6.5）。
#1 规划器 / #3 记忆 / #4 执行引擎尚未实现，以 Protocol 定义边界，
sim.py 提供 mock 实现，使调度器可独立运行与测试。"""
from __future__ import annotations
from typing import Protocol, Optional
from core.scheduler.models import Subtask, ScheduleDecision


class ExecutionResult:
    """#4 执行引擎返回的执行结果。"""

    def __init__(self, success: bool, latency_ms: float, cost: float,
                 tokens: int, note: str = ""):
        self.success = success
        self.latency_ms = latency_ms
        self.cost = cost
        self.tokens = tokens
        self.note = note

    def __repr__(self) -> str:
        return (f"ExecutionResult(success={self.success}, "
                f"latency_ms={self.latency_ms:.0f}, cost={self.cost:.3f})")


class PlannerPort(Protocol):
    """#1 规划器：流式输出子任务 DAG 的节点。"""
    def next_subtask(self) -> Optional[Subtask]: ...


class MemoryPort(Protocol):
    """#3 记忆：提供当前工作上下文规模（影响 s_w 估计）。"""
    def current_context_tokens(self) -> int: ...


class ExecutorPort(Protocol):
    """#4 执行引擎：按调度决策执行子任务。"""
    def execute(self, w: Subtask, decision: ScheduleDecision) -> ExecutionResult: ...
