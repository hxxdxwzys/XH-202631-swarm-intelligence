"""bandit 在线学习测试。cd code && python -m unittest core.scheduler.tests.test_bandit"""
import unittest
from core.scheduler.models import ComputeScale, LatencyTier, SensitivityLevel, Subtask
from core.scheduler.bandit import ContextualBandit
from core.scheduler.adaptive import AdaptiveScheduler
from core.scheduler.sim import default_env, LocalSimExecutor


class TestBandit(unittest.TestCase):
    def setUp(self):
        self.env = default_env()
        self.exec = LocalSimExecutor(self.env, seed=1)
        self.sched = AdaptiveScheduler(self.env, self.exec, ContextualBandit(c=0.1))

    def _task(self):
        return Subtask("t", ComputeScale.S2_HEAVY, LatencyTier.T2_MINUTE,
                       SensitivityLevel.L1_INTERNAL, est_input_tok=5000, est_output_tok=2000)

    def test_converges_to_best_arm(self):
        """重复同类任务，bandit 应收敛到质量最高的可行 arm（云端 30B）。"""
        picks = []
        for _ in range(20):
            w = self._task()
            d = self.sched.schedule(w)
            r = self.exec.execute(w, d)
            self.sched.feedback(w, d, r)
            picks.append(d.model_name)
        self.assertGreaterEqual(picks.count("Qwen3-30B"), 15)
        self.assertLessEqual(picks.count("Qwen3-8B"), 5)

    def test_context_isolated(self):
        """不同上下文的统计互不影响。"""
        for _ in range(5):
            w = self._task()
            d = self.sched.schedule(w)
            self.sched.feedback(w, d, self.exec.execute(w, d))
        # 另一上下文统计应为空
        other = (ComputeScale.S0_LIGHT, SensitivityLevel.L2_SENSITIVE)
        self.assertEqual(self.sched.bandit.arm_distribution(other), {})


if __name__ == "__main__":
    unittest.main()
