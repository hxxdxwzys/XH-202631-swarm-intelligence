"""调度器单元测试。运行：cd code && python -m unittest core.scheduler.tests.test_scheduler"""
import unittest
from core.scheduler.models import (
    ComputeScale, LatencyTier, SensitivityLevel, Subtask, ScheduleDecision,
)
from core.scheduler.scheduler import Scheduler
from core.scheduler.metrics import privacy_satisfaction
from core.scheduler.sim import default_env, LocalSimExecutor


class TestScheduler(unittest.TestCase):
    def setUp(self):
        self.env = default_env()
        self.sched = Scheduler(self.env, LocalSimExecutor(self.env))

    def _decide(self, **kw):
        w = Subtask(id=kw.pop("id", "t"), **kw)
        return self.sched.schedule(w)

    def test_public_heavy_splits_across_layers(self):
        """公开·超重：48B 单层放不下 → 端边云层切分。"""
        d = self._decide(scale=ComputeScale.S3_XHEAVY,
                         latency_tier=LatencyTier.T3_BATCH,
                         sensitivity=SensitivityLevel.L0_PUBLIC,
                         est_input_tok=8000, est_output_tok=4000)
        self.assertTrue(d.feasible)
        self.assertIsNotNone(d.split)
        self.assertEqual(d.split.mode, "layer")
        participating = [n for n, b in d.split.block_allocation if b > 0]
        self.assertGreaterEqual(len(participating), 2)
        # 切分块数守恒
        total_blocks = sum(b for _, b in d.split.block_allocation)
        self.assertEqual(total_blocks, 48)

    def test_confidential_light_goes_end(self):
        """机密·轻量·交互 → 仅端侧可承载。"""
        d = self._decide(scale=ComputeScale.S0_LIGHT,
                         latency_tier=LatencyTier.T0_INTERACTIVE,
                         sensitivity=SensitivityLevel.L3_CONFIDENTIAL,
                         est_input_tok=60, est_output_tok=20)
        self.assertTrue(d.feasible)
        self.assertEqual(self.env.by_name(d.layer_name).kind, "end")

    def test_sensitive_never_cloud(self):
        """敏感任务（L2）任何情况下都不分配到云端。"""
        for scale in (ComputeScale.S0_LIGHT, ComputeScale.S1_MEDIUM):
            d = self._decide(scale=scale, latency_tier=LatencyTier.T2_MINUTE,
                             sensitivity=SensitivityLevel.L2_SENSITIVE,
                             est_input_tok=500, est_output_tok=200)
            if d.feasible:
                self.assertIn(self.env.by_name(d.layer_name).kind, ("end", "edge"))

    def test_internal_heavy_goes_cloud(self):
        """内部·重型 → 云端大模型。"""
        d = self._decide(scale=ComputeScale.S2_HEAVY,
                         latency_tier=LatencyTier.T2_MINUTE,
                         sensitivity=SensitivityLevel.L1_INTERNAL,
                         est_input_tok=5000, est_output_tok=2000)
        self.assertTrue(d.feasible)
        self.assertEqual(self.env.by_name(d.layer_name).kind, "cloud")

    def test_sensitive_medium_goes_edge(self):
        """敏感·中等 → 边缘（云被禁）。"""
        d = self._decide(scale=ComputeScale.S1_MEDIUM,
                         latency_tier=LatencyTier.T2_MINUTE,
                         sensitivity=SensitivityLevel.L2_SENSITIVE,
                         est_input_tok=1000, est_output_tok=500)
        self.assertTrue(d.feasible)
        self.assertIn(self.env.by_name(d.layer_name).kind, ("end", "edge"))

    def test_confidential_heavy_infeasible(self):
        """机密·重型 → 端侧无法承载且不可切分 → 不可行（回送重规划）。"""
        d = self._decide(scale=ComputeScale.S2_HEAVY,
                         latency_tier=LatencyTier.T2_MINUTE,
                         sensitivity=SensitivityLevel.L3_CONFIDENTIAL,
                         est_input_tok=4000, est_output_tok=2000)
        self.assertFalse(d.feasible)

    def test_confidential_never_on_cloud(self):
        """机密任务任何情况下都不分配到云端。"""
        for scale in ComputeScale:
            for tier in LatencyTier:
                d = self._decide(scale=scale, latency_tier=tier,
                                 sensitivity=SensitivityLevel.L3_CONFIDENTIAL,
                                 est_input_tok=500, est_output_tok=200)
                if d.feasible:
                    self.assertNotEqual(self.env.by_name(d.layer_name).kind, "cloud")

    def test_privacy_satisfaction_full(self):
        """调度器尊重隐私约束时，P_priv = 100%。"""
        subtasks = [
            Subtask("a", ComputeScale.S0_LIGHT, LatencyTier.T0_INTERACTIVE,
                    SensitivityLevel.L2_SENSITIVE, 60, 20),
            Subtask("b", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L1_INTERNAL, 5000, 2000),
            Subtask("c", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L2_SENSITIVE, 1000, 500),
        ]
        decisions = [self.sched.schedule(w) for w in subtasks]
        self.assertEqual(privacy_satisfaction(decisions, subtasks, self.env), 1.0)


if __name__ == "__main__":
    unittest.main()
