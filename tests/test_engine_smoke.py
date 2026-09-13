"""Smoke test — MockAthlete genuinely solves the IOC drills, so a green
run means the engine, checks, fault injection, and ledger all work."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gym.athlete import MockAthlete
from gym.engine import run_drill
from gym.ledger import Ledger, read_all
from gym.scheduler import prescribe
from gym.scoring import recovery_index, report

ROOT = Path(__file__).resolve().parents[1]


class GymSmokeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.athlete = MockAthlete()

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, drill):
        ledger = Ledger(self.tmp.name)
        summary = run_drill(ROOT / drill, self.athlete, ledger, verbose=False)
        return summary, ledger

    def test_precision_drill_clean_pass(self):
        summary, ledger = self._run("drills/precision/log_triage_01.json")
        self.assertEqual(summary["mean_score"], 1.0)
        self.assertEqual(summary["budget_breaches"], 0)
        entries = read_all(self.tmp.name)
        self.assertEqual(len(entries), 12)  # 3 sets x 4 reps

    def test_conditioning_drill_with_noise_progression(self):
        summary, _ = self._run("drills/conditioning/ctx_stamina_01.json")
        self.assertEqual(summary["mean_score"], 1.0)

    def test_reaction_drill_fault_reps_logged(self):
        summary, ledger = self._run("drills/reaction/tool_outage_01.json")
        entries = read_all(ledger.dir)
        fault_reps = [e for e in entries if e["fault"]]
        self.assertTrue(fault_reps, "fault reps must be recorded")
        self.assertEqual(recovery_index(read_all(ledger.dir), "mock"), 1.0)

    def test_scheduler_and_scoreboard(self):
        self._run("drills/precision/log_triage_01.json")
        rx = prescribe(self.tmp.name, "mock", str(ROOT / "drills"))
        self.assertIn(rx["next_drill"], {"ctx_stamina_01", "tool_outage_01"})
        board = report(self.tmp.name, "mock")
        self.assertEqual(board["session_means"], [1.0])
        self.assertEqual(board["improvement_velocity"], 0.0)  # one session

    def test_ledger_is_append_only_jsonl(self):
        _, ledger = self._run("drills/precision/log_triage_01.json")
        with open(ledger.path, encoding="utf-8") as fh:
            for line in fh:
                entry = json.loads(line)
                for key in ("ts", "omega_tier", "athlete_id", "drill_id",
                            "set", "rep", "score", "passed", "failures"):
                    self.assertIn(key, entry)


if __name__ == "__main__":
    unittest.main(verbosity=2)
