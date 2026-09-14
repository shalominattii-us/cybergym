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

    def test_lmstudio_adapter_against_stub_server(self):
        """Device is off in dev, so verify against an in-process stub that
        speaks LM Studio's OpenAI-compatible API (:1234 shape)."""
        import threading
        from http.server import BaseHTTPRequestHandler, HTTPServer

        from gym.athlete import LMStudioAthlete

        class Stub(BaseHTTPRequestHandler):
            def _send(self, obj):
                body = json.dumps(obj).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self._send({"data": [{"id": "heretic-test-model"}]})

            def do_POST(self):
                self._send({"choices": [{"message": {"content": "IOC: 203.0.113.44"}}]})

            def log_message(self, *args):
                pass

        server = HTTPServer(("127.0.0.1", 0), Stub)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            athlete = LMStudioAthlete(host=f"http://127.0.0.1:{server.server_port}")
            self.assertEqual(athlete.athlete_id, "lmstudio:heretic-test-model")
            self.assertIn("203.0.113.44", athlete.complete("p", {"input": "x"}))
        finally:
            server.shutdown()

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
