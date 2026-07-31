"""DAG 运行时测试（v0.4）。cd code && python -m unittest core.scheduler.tests.test_runtime"""
import unittest
from core.scheduler.models import (
    ComputeScale, LatencyTier, SensitivityLevel, Subtask,
)
from core.scheduler.runtime import SchedulerRuntime
from core.scheduler.sim import default_env, LocalSimExecutor


class TestRuntime(unittest.TestCase):
    def setUp(self):
        self.env = default_env()
        self.exec = LocalSimExecutor(self.env)
        self.rt = SchedulerRuntime(self.env, self.exec)

    def _dag(self):
        """A→B→D, A→C→D 的菱形 DAG。"""
        return [
            Subtask("A", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500),
            Subtask("B", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 5000, 2000, depends_on=("A",)),
            Subtask("C", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500, depends_on=("A",)),
            Subtask("D", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500, depends_on=("B", "C")),
        ]

    def test_dag_completes(self):
        """完整 DAG 应全部完成。"""
        result = self.rt.run(self._dag())
        self.assertEqual(result["completed"], 4)
        self.assertEqual(result["failed"], 0)

    def test_dependency_order(self):
        """A 必须先于 B/C/D 完成（step 序号更小）。"""
        result = self.rt.run(self._dag())
        steps = {}
        for i, d in enumerate(result["decisions"]):
            steps[d.subtask_id] = i
        self.assertLess(steps["A"], steps["B"])
        self.assertLess(steps["A"], steps["C"])
        self.assertLess(steps["B"], steps["D"])
        self.assertLess(steps["C"], steps["D"])

    def test_parallel_batch(self):
        """B 和 C 依赖相同（A），应同批调度（step 相邻）。"""
        result = self.rt.run(self._dag())
        steps = {}
        for i, d in enumerate(result["decisions"]):
            steps[d.subtask_id] = i
        # B 和 C 在同一批，step 相邻
        self.assertEqual(abs(steps["B"] - steps["C"]), 1)

    def test_critical_path_returned(self):
        """关键路径应包含 A、B、D（A→B→D 比 A→C→D 长）。"""
        result = self.rt.run(self._dag())
        cp = result["critical_path"]
        self.assertIn("A", cp)
        self.assertIn("B", cp)
        self.assertIn("D", cp)
        self.assertNotIn("C", cp)

    def test_deadlock_on_infeasible(self):
        """上游不可行时，下游应被标记失败（死锁检测）。"""
        # 机密重型 → 端侧不可承载 → 不可行
        dag = [
            Subtask("X", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L3_CONFIDENTIAL, 4000, 2000),
            Subtask("Y", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500, depends_on=("X",)),
        ]
        result = self.rt.run(dag)
        self.assertEqual(result["failed"], 2)  # X 不可行 → Y 死锁

    def test_event_log_populated(self):
        """运行后事件日志应有记录。"""
        result = self.rt.run(self._dag())
        self.assertEqual(result["summary"]["n"], 4)


if __name__ == "__main__":
    unittest.main()
