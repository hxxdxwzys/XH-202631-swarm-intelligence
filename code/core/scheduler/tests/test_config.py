"""配置加载测试。cd code && python -m unittest core.scheduler.tests.test_config"""
import os
import unittest
from core.scheduler.config import env_from_dict, load_env


class TestConfig(unittest.TestCase):
    def test_env_from_dict(self):
        d = {"layers": [
            {"name": "端", "kind": "end", "compute_tps": 100, "mem_gb": 8,
             "rtt_ms": 2, "cost_per_1k_tok": 0,
             "models": [{"name": "M1", "param_b": 1.5, "context_window": 4096,
                         "capability": 0.5, "blocks": 24}]},
            {"name": "云", "kind": "cloud", "compute_tps": 1000, "mem_gb": 80,
             "rtt_ms": 50, "cost_per_1k_tok": 0.01,
             "models": [{"name": "M2", "param_b": 30, "context_window": 32768,
                         "capability": 0.9, "blocks": 48}]},
        ]}
        env = env_from_dict(d)
        self.assertEqual(len(env.layers), 2)
        self.assertEqual(env.by_kind("cloud").find_model("M2").param_b, 30)
        self.assertEqual(env.by_name("端").kind, "end")

    def test_load_env_json(self):
        here = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(os.path.dirname(here), "default_env.json")
        env = load_env(json_path)
        self.assertEqual(len(env.layers), 3)
        self.assertIsNotNone(env.by_kind("cloud").find_model("Qwen3-30B"))


if __name__ == "__main__":
    unittest.main()
