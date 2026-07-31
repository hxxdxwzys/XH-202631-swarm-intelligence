"""DAG 感知运行时（v0.4）— 从"一次调一个"升级为"按 DAG 拓扑序驱动整条流水线"。

核心循环：
1. 找就绪子任务（depends_on 全完成）
2. 批量调度（BatchScheduler LPT 均衡）
3. 逐个执行 → 标记完成/失败
4. 完成后重评估下游就绪性 → 回到 1
5. 全部完成或死锁（上游失败导致下游无法就绪）则结束

关键路径感知：运行前识别 DAG 关键路径，用于演示与后续 v0.5 优先调度。
对应赛题"完整性 / 系统基础与闭环"（15分）。"""
from __future__ import annotations
from core.scheduler.models import Subtask, ScheduleDecision, ResourceEnvironment
from core.scheduler.balancer import BatchScheduler, critical_path
from core.scheduler.events import ScheduleLogger
from core.scheduler.ports import ExecutorPort


class SchedulerRuntime:
    """DAG 感知调度运行时：驱动子任务 DAG 端到端执行。"""

    def __init__(self, env: ResourceEnvironment, executor: ExecutorPort,
                 scheduler: BatchScheduler | None = None,
                 logger: ScheduleLogger | None = None):
        self.env = env
        self.executor = executor
        self.sched = scheduler or BatchScheduler(env, executor)
        self.logger = logger or ScheduleLogger()

    def run(self, dag: list[Subtask]) -> dict:
        """运行完整 DAG，返回汇总统计。

        dag: 子任务列表，每个带 depends_on 指向前驱 ID。
        返回: {total, completed, failed, critical_path, steps, summary}
        """
        pending = list(dag)
        completed: set[str] = set()
        failed: set[str] = set()
        all_decisions: list[ScheduleDecision] = []
        step = 0

        # 识别关键路径（用于展示与后续优先调度）
        cp = critical_path(dag, lambda w: self._predict_latency(w))

        while pending:
            # 找就绪子任务（所有依赖均已完成）
            ready = [w for w in pending
                     if all(d in completed for d in w.depends_on)]

            if not ready:
                # 死锁：剩余任务的上游有失败 → 标记为失败
                for w in pending:
                    failed.add(w.id)
                break

            # 批量调度就绪任务（LPT makespan 优化）
            decisions = self.sched.schedule_batch(ready)

            for w, d in zip(ready, decisions):
                self.logger.log(d, step)
                step += 1
                if d.feasible:
                    result = self.executor.execute(w, d)
                    if result.success:
                        completed.add(w.id)
                    else:
                        failed.add(w.id)
                else:
                    failed.add(w.id)

            all_decisions.extend(decisions)
            pending = [w for w in pending
                       if w.id not in completed and w.id not in failed]

        return {
            "total": len(dag),
            "completed": len(completed),
            "failed": len(failed),
            "critical_path": cp,
            "steps": step,
            "decisions": all_decisions,
            "summary": self.logger.summary(),
        }

    def _predict_latency(self, w: Subtask) -> float:
        """预估子任务最小时延（用于关键路径计算）。"""
        _, feasible = self.sched._feasible(w)
        if feasible:
            return min(lat for _, _, lat in feasible)
        return 1000.0  # 不可行时的默认估值

    def run_verbose(self, dag: list[Subtask]) -> dict:
        """运行 DAG 并打印逐步执行轨迹。"""
        result = self.run(dag)
        print(f"DAG 共 {result['total']} 个子任务，"
              f"关键路径: {result['critical_path']}")
        print(f"完成 {result['completed']}，失败 {result['failed']}，"
              f"调度步数 {result['steps']}")
        print(f"汇总: {result['summary']}")
        return result
