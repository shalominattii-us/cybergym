"""The ledger — append-only, rep-by-rep training log.

Vault protocol applies: every session timestamped, Omega-tiered, preserved.
One JSONL file per session under the ledger dir. Nothing is ever rewritten;
corrections are new lines.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path


def new_session_id() -> str:
    return time.strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


class Ledger:
    def __init__(self, ledger_dir: str | Path, session_id: str | None = None):
        self.dir = Path(ledger_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.session_id = session_id or new_session_id()
        self.path = self.dir / f"{self.session_id}.jsonl"

    def record(self, *, omega_tier: str, athlete_id: str, drill_id: str,
               set_no: int, rep: int, score: float, passed: bool,
               failures: list[str], fault: bool = False,
               elapsed_ms: int = 0, notes: str = "") -> dict:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "session_id": self.session_id,
            "omega_tier": omega_tier,
            "athlete_id": athlete_id,
            "drill_id": drill_id,
            "set": set_no,
            "rep": rep,
            "score": round(score, 4),
            "passed": passed,
            "failures": failures,
            "fault": fault,
            "elapsed_ms": elapsed_ms,
            "notes": notes,
        }
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        return entry


def read_all(ledger_dir: str | Path) -> list[dict]:
    entries = []
    for path in sorted(Path(ledger_dir).glob("*.jsonl")):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    return entries
