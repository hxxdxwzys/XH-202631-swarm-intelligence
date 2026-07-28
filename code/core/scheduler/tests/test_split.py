"""切分测试：层切分 + 阶段切分。cd code && python -m unittest core.scheduler.tests.test_split"""
import unittest
from core.scheduler.models import (
    ComputeScale, LatencyTier, SensitivityLevel, Subtask,
)
from core.scheduler.split import best_layer_split, best_phase_split
from core.scheduler.sim import default_env


class TestSplit(unittest.TestCase):
    def setUp(self):
        self.env = default_env()

    def test_layer_split_block_conservation(self):
        """层切分：块数守恒，至少两层参与。"""
        m = self.env.by_kind("cloud").find_model("Mega-48B")
        w = Subtask("w", ComputeScale.S3_XHEAVY, LatencyTier.T3_BATCH,
                    SensitivityLevel.L0_PUBLIC, 8000, 4000)
        plan = best_layer_split(w, m, self.env, ("end", "edge", "cloud"))
        self.assertIsNotNone(plan)
        self.assertEqual(sum(b for _, b in plan.block_allocation), m.blocks)
        participating = [n for n, b in plan.block_allocation if b > 0]
        self.assertGreaterEqual(len(participating), 2)

    def test_phase_split_two_distinct_layers(self):
        """阶段切分：返回两个不同层（均能承载模型权重）。"""
        m = self.env.by_kind("edge").find_model("Qwen3-8B")  # 8B fits edge+cloud
        w = Subtask("w", ComputeScale.S1_MEDIUM, LatencyTier.T2_MINUTE,
                    SensitivityLevel.L0_PUBLIC, 1000, 500)
        plan = best_phase_split(w, m, self.env, ("end", "edge", "cloud"))
        self.assertIsNotNone(plan)
        self.assertEqual(plan.mode, "phase")
        self.assertEqual(len(plan.phase_layers), 2)
        self.assertNotEqual(plan.phase_layers[0], plan.phase_layers[1])

    def test_phase_split_infeasible_when_no_two_fit(self):
        """48B 没有任何单层能承载 → 阶段切分不可行。"""
        m = self.env.by_kind("cloud").find_model("Mega-48B")
        w = Subtask("w", ComputeScale.S3_XHEAVY, LatencyTier.T3_BATCH,
                    SensitivityLevel.L0_PUBLIC, 8000, 4000)
        plan = best_phase_split(w, m, self.env, ("end", "edge", "cloud"))
        self.assertIsNone(plan)


if __name__ == "__main__":
    unittest.main()
