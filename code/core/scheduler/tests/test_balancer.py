"""时间均衡测试（v0.3）。cd code && python -m unittest core.scheduler.tests.test_balancer"""
import unittest
from core.scheduler.models import (
    ComputeScale, LatencyTier, SensitivityLevel, Subtask,
)
from core.scheduler.balancer import BatchScheduler, LoadTracker, critical_path
from core.scheduler.metrics import makespan, load_balance_index, idle_ratio
from core.scheduler.sim import default_env, LocalSimExecutor


class TestBalancer(unittest.TestCase):
    def setUp(self):
        self.env = default_env()
        self.exec = LocalSimExecutor(self.env)
        self.sched = BatchScheduler(self.env, self.exec)

    def _task(self, i, scale=ComputeScale.S1_MEDIUM, sens=SensitivityLevel.L0_PUBLIC,
              ti=1000, to=500):
        sid = i if isinstance(i, str) else f"t{i}"
        return Subtask(sid, scale, LatencyTier.T2_MINUTE, sens, ti, to)

    def test_batch_makespan_better_than_all_cloud(self):
        """批量调度 makespan 应优于全部堆云端的串行时间。"""
        tasks = [self._task(i) for i in range(9)]
        decisions = self.sched.schedule_batch(tasks)
        ms = makespan(self.sched.tracker.loads())
        # 全部堆云端串行 = 9 × 810ms = 7290ms
        self.assertLess(ms, 7290.0)
        # 至少用了 2 层
        used = {d.layer_name for d in decisions if d.feasible}
        self.assertGreaterEqual(len(used), 2)

    def test_load_balance_improves(self):
        """批量调度的负载均衡度应高于全堆一层（>0.4）。"""
        tasks = [self._task(i) for i in range(9)]
        self.sched.schedule_batch(tasks)
        idx = load_balance_index(self.sched.tracker.loads())
        # 全堆一层的均衡度 = 1/3 ≈ 0.333；批量应明显更高
        self.assertGreater(idx, 0.4)

    def test_idle_ratio_decreases(self):
        """批量调度的空闲率应低于全堆一层。"""
        tasks = [self._task(i) for i in range(9)]
        self.sched.schedule_batch(tasks)
        ir = idle_ratio(self.sched.tracker.loads())
        # 全堆一层空闲率 = 2/3 ≈ 0.667；批量应更低
        self.assertLess(ir, 0.6)

    def test_lpt_heaviest_to_fastest(self):
        """LPT：最重任务应先派到最快层（云端）。"""
        tasks = [
            self._task("light", ComputeScale.S0_LIGHT, ti=100, to=50),
            self._task("heavy", ComputeScale.S2_HEAVY, ti=5000, to=2000),
        ]
        decisions = self.sched.schedule_batch(tasks)
        by_id = {d.subtask_id: d for d in decisions}
        self.assertEqual(by_id["heavy"].layer_name, "云端")

    def test_privacy_respected_in_batch(self):
        """批量调度仍尊重隐私约束：机密任务只到端侧。"""
        tasks = [self._task(i, sens=SensitivityLevel.L3_CONFIDENTIAL) for i in range(3)]
        decisions = self.sched.schedule_batch(tasks)
        for d in decisions:
            if d.feasible:
                self.assertEqual(self.env.by_name(d.layer_name).kind, "end")

    def test_critical_path_identification(self):
        """DAG 关键路径：A→B→D 比 A→C→D 长，B 在关键路径上、C 不在。"""
        A = Subtask("A", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500)
        B = Subtask("B", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 5000, 2000, depends_on=("A",))
        C = Subtask("C", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500, depends_on=("A",))
        D = Subtask("D", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500,
                    depends_on=("B", "C"))
        lat = {"A": 810, "B": 3560, "C": 810, "D": 810}
        cp = critical_path([A, B, C, D], lambda w: lat[w.id])
        self.assertIn("A", cp)
        self.assertIn("B", cp)
        self.assertIn("D", cp)
        self.assertNotIn("C", cp)

    def test_load_tracker_basic(self):
        """LoadTracker 基本操作。"""
        t = LoadTracker(["a", "b"])
        t.assign("a", 100)
        t.assign("a", 50)
        t.assign("b", 200)
        self.assertEqual(t.load_of("a"), 150)
        self.assertEqual(t.load_of("b"), 200)
        self.assertEqual(t.earliest_finish("a"), 150)
        t.finish("a", 100)
        self.assertEqual(t.load_of("a"), 50)
        t.reset()
        self.assertEqual(t.load_of("a"), 0)


if __name__ == "__main__":
    unittest.main()
