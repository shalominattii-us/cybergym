"""Autonomy loop — the gym runs itself.

Waits for the local model server (LM Studio :1234 or Ollama :11434),
asks the front desk what to train, runs the drill, records to the ledger,
sleeps, repeats. No human in the loop — this is the unattended mode the
sovereign stack is built for.

Usage (on the unit):
    python scripts/gym_loop.py --athlete lmstudio --interval 1800
    python scripts/gym_loop.py --athlete lmstudio --once   # single session

Stops on Ctrl+C. Every session lands in ledger/ as timestamped JSONL —
the vault protocol: nothing is lost, everything is attributable.
"""

from __future__ import annotations

import argparse
import sys
import time
import traceback
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gym.athlete import get_athlete
from gym.engine import run_drill
from gym.ledger import Ledger
from gym.scheduler import prescribe

HEALTH = {
    "lmstudio": "http://localhost:1234/v1/models",
    "ollama": "http://localhost:11434/api/tags",
}


def wait_for_server(athlete_spec: str, timeout_s: int = 900) -> None:
    """Block until the model server answers. The unit takes a while to
    load a MOE into memory — be patient, poll quietly."""
    url = HEALTH.get(athlete_spec)
    if not url:
        return  # mock/groq/aegentis need no local server
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                if resp.status == 200:
                    print(f"[loop] server up: {url}")
                    return
        except Exception:
            pass
        time.sleep(10)
    raise TimeoutError(f"{athlete_spec} server not answering after {timeout_s}s")


def session(athlete_spec: str, model: str | None, root: Path) -> dict:
    """One workout: front desk prescribes, engine executes, ledger records."""
    athlete = get_athlete(athlete_spec, model)
    ledger = Ledger(root / "ledger")
    plan = prescribe(str(root / "ledger"), athlete.athlete_id, str(root / "drills"))
    drill = plan.get("next_drill")
    if not drill:
        return {"status": "idle", "reason": "no drills on the floor"}
    drill_path = root / "drills" / f"{drill.split('_')[0]}"  # resolved below
    # drill ids are <name>_<nn>; find the file by id anywhere under drills/
    matches = list((root / "drills").rglob(f"{drill}.json"))
    if not matches:
        return {"status": "idle", "reason": f"drill file for {drill} not found"}
    print(f"[loop] workout: {drill} ({plan['reason']})")
    summary = run_drill(matches[0], athlete, ledger)
    summary["prescribed_because"] = plan["reason"]
    return summary


def main():
    ap = argparse.ArgumentParser(prog="cybergym-loop")
    ap.add_argument("--athlete", default="lmstudio",
                    choices=["mock", "ollama", "lmstudio", "groq", "aegentis"])
    ap.add_argument("--model", default=None,
                    help="override model id; default = whatever is loaded")
    ap.add_argument("--root", default=None,
                    help="gym root (default: repo root)")
    ap.add_argument("--interval", type=int, default=1800,
                    help="seconds between workouts (default 1800)")
    ap.add_argument("--once", action="store_true",
                    help="run one workout and exit")
    args = ap.parse_args()

    root = Path(args.root) if args.root else Path(__file__).resolve().parents[1]
    print(f"[loop] CyberGym autonomy — athlete={args.athlete} root={root}")
    wait_for_server(args.athlete)

    while True:
        try:
            result = session(args.athlete, args.model, root)
            print(f"[loop] done: {result}")
        except Exception:
            # The loop must not die because one workout did. Log and continue.
            print("[loop] workout failed:")
            traceback.print_exc()
        if args.once:
            break
        print(f"[loop] resting {args.interval}s before next workout")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
