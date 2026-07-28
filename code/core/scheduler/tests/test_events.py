"""事件日志测试。cd code && python -m unittest core.scheduler.tests.test_events"""
import json
import os
import tempfile
import unittest
from core.scheduler.models import ScheduleDecision, SplitPlan
from core.scheduler.events import ScheduleLogger


class TestEvents(unittest.TestCase):
    def _decisions(self):
        return [
            ScheduleDecision("x", "终端", "Qwen3-3B", None, 402.0, 0.0, True, ""),
            ScheduleDecision("y", "云端", "Mega-48B",
                             SplitPlan("layer", (("边缘", 8), ("云端", 40))),
                             8473.0, 0.124, True, "layer-split"),
            ScheduleDecision("z", "", "", None, 0.0, 0.0, False, "infeasible"),
        ]

    def test_jsonl_write_and_summary(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "ev.jsonl")
            logger = ScheduleLogger(path=path)
            for i, d in enumerate(self._decisions()):
                logger.log(d, i)
            logger.write_jsonl()
            with open(path, encoding="utf-8") as f:
                lines = [json.loads(l) for l in f if l.strip()]
            self.assertEqual(len(lines), 3)
            self.assertEqual(lines[1]["split_mode"], "layer")
            self.assertEqual(lines[2]["feasible"], False)
            s = logger.summary()
            self.assertEqual(s["n"], 3)
            self.assertEqual(s["feasible"], 2)
            self.assertEqual(s["infeasible"], 1)
            self.assertEqual(s["splits"], 1)


if __name__ == "__main__":
    unittest.main()
