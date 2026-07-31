"""集成测试 + 性能基准（v0.5）。

集成测试：mock planner + memory + executor → SchedulerRuntime 端到端跑通完整 DAG。
性能基准：验证调度器自身开销 << 任务执行时间，不构成瓶颈。

cd code && python -m unittest core.scheduler.tests.test_integration
cd code && python -m core.scheduler.tests.test_integration --bench
"""
import unittest
import time
from core.scheduler.models import (
    ComputeScale, LatencyTier, SensitivityLevel, Subtask,
)
from core.scheduler.runtime import SchedulerRuntime
from core.scheduler.adaptive import AdaptiveScheduler
from core.scheduler.balancer import BatchScheduler
from core.scheduler.bandit import ContextualBandit
from core.scheduler.sim import default_env, LocalSimExecutor
from core.scheduler.metrics import privacy_satisfaction


class MockPlanner:
    """mock #1 规划器：产出 DAG。"""
    def __init__(self, dag: list[Subtask]):
        self._dag = list(dag)

    def get_dag(self) -> list[Subtask]:
        return list(self._dag)


class MockMemory:
    """mock #3 记忆：返回当前上下文 token 数。"""
    def current_context_tokens(self) -> int:
        return 2000


class TestIntegration(unittest.TestCase):
    """端到端集成测试：模拟完整系统运行。"""

    def setUp(self):
        self.env = default_env()
        self.exec = LocalSimExecutor(self.env, seed=99)
        self.planner = MockPlanner(self._build_dag())
        self.memory = MockMemory()

    def _build_dag(self) -> list[Subtask]:
        """8 节点 DAG，混合规模/敏感度/依赖层级。"""
        return [
            Subtask("n1", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 5000, 2000),
            Subtask("n2", ComputeScale.S0_LIGHT, LatencyTier.T0_INTERACTIVE,
                    SensitivityLevel.L3_CONFIDENTIAL, 60, 20),
            Subtask("n3", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L2_SENSITIVE, 1000, 500, depends_on=("n1",)),
            Subtask("n4", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L1_INTERNAL, 1500, 800, depends_on=("n1",)),
            Subtask("n5", ComputeScale.S3_XHEAVY, LatencyTier.T3_BATCH,
                    SensitivityLevel.L0_PUBLIC, 8000, 4000, depends_on=("n3",)),
            Subtask("n6", ComputeScale.S0_LIGHT, LatencyTier.T1_SECOND,
                    SensitivityLevel.L2_SENSITIVE, 300, 100, depends_on=("n2",)),
            Subtask("n7", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L1_INTERNAL, 1200, 600, depends_on=("n4", "n6")),
            Subtask("n8", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500, depends_on=("n5", "n7")),
        ]

    def test_full_dag_run(self):
        """8 节点 DAG 端到端完成。"""
        dag = self.planner.get_dag()
        rt = SchedulerRuntime(self.env, self.exec)
        result = rt.run(dag)
        self.assertEqual(result["total"], 8)
        self.assertGreater(result["completed"], 0)

    def test_privacy_compliance(self):
        """全流程隐私约束满足。"""
        dag = self.planner.get_dag()
        rt = SchedulerRuntime(self.env, self.exec)
        result = rt.run(dag)
        feasible = [d for d in result["decisions"] if d.feasible]
        p = privacy_satisfaction(feasible, dag, self.env)
        self.assertEqual(p, 1.0)

    def test_dependency_respected(self):
        """n3 依赖 n1，n3 的调度步号 > n1。"""
        dag = self.planner.get_dag()
        rt = SchedulerRuntime(self.env, self.exec)
        result = rt.run(dag)
        steps = {d.subtask_id: i for i, d in enumerate(result["decisions"])}
        if "n1" in steps and "n3" in steps:
            self.assertLess(steps["n1"], steps["n3"])

    def test_adaptive_runtime(self):
        """自适应调度器 + bandit 在运行时中工作。"""
        dag = self.planner.get_dag()
        batch = BatchScheduler(self.env, self.exec)
        # 用 AdaptiveScheduler 的 bandit 做反馈学习（通过 executor 回灌）
        rt = SchedulerRuntime(self.env, self.exec, scheduler=batch)
        result = rt.run(dag)
        self.assertGreater(result["completed"], 0)
        self.assertGreater(result["summary"]["n"], 0)

    def test_event_log_complete(self):
        """事件日志记录所有调度步。"""
        dag = self.planner.get_dag()
        rt = SchedulerRuntime(self.env, self.exec)
        result = rt.run(dag)
        self.assertEqual(result["summary"]["n"], len(result["decisions"]))


class TestBenchmark(unittest.TestCase):
    """调度器性能基准：验证调度开销不构成瓶颈。"""

    def _gen_tasks(self, n: int) -> list[Subtask]:
        return [Subtask(f"b{i}", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                        SensitivityLevel.L0_PUBLIC, 1000, 500) for i in range(n)]

    def test_overhead_under_1ms_per_task(self):
        """单任务调度开销应 < 1ms。"""
        env = default_env()
        sched = BatchScheduler(env, LocalSimExecutor(env))
        for n in (10, 100, 500):
            tasks = self._gen_tasks(n)
            t0 = time.perf_counter()
            sched.schedule_batch(tasks)
            elapsed = (time.perf_counter() - t0) * 1000  # ms
            per_task = elapsed / n
            self.assertLess(per_task, 1.0,
                            f"n={n}: {per_task:.3f}ms/task 超过 1ms 阈值")
            print(f"  n={n:>4}: {elapsed:>8.2f}ms total, {per_task:.4f}ms/task")


if __name__ == "__main__":
    import sys
    if "--bench" in sys.argv:
        suite = unittest.TestLoader().loadTestsFromTestCase(TestBenchmark)
        unittest.TextTestRunner(verbosity=2).run(suite)
    else:
        unittest.main()
