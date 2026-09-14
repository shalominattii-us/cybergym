"""Drill engine — Omega Pre core.

Loads a drill definition (JSON), runs sets x reps against an Athlete,
scores each rep with deterministic checks, injects faults for reaction
drills, and writes every rep to the ledger.

A drill is judged like a lifting program: reps, sets, progression.

Usage:
    python -m gym.engine run --drill drills/precision/log_triage_01.json --athlete mock
    python -m gym.engine run --drill drills/reaction/tool_outage_01.json --athlete ollama --model llama3.1:8b
"""

from __future__ import annotations

import argparse
import json
import random
import re
import time
from pathlib import Path

from .athlete import get_athlete
from .ledger import Ledger


def _noise_lines(n: int, seed: int) -> str:
    """Benign log filler used to escalate difficulty (longer context,
    more distractors) as sets progress."""
    rng = random.Random(seed)
    hosts = ["ws-04", "ws-11", "print-02", "nas-01", "vpn-gw"]
    users = ["svc_backup", "j.chen", "a.okafor", "cron", "m.reyes"]
    lines = []
    for _ in range(n):
        lines.append(
            f"Sep 11 03:{rng.randint(10,59)}:{rng.randint(10,59)} "
            f"{rng.choice(hosts)} sshd[{rng.randint(1000,9999)}]: "
            f"Accepted publickey for {rng.choice(users)} from "
            f"10.0.{rng.randint(0,8)}.{rng.randint(2,250)} port {rng.randint(20000,60000)}"
        )
    return "\n".join(lines)


def _check(expect: dict, response: str) -> tuple[float, list[str]]:
    """Deterministic rep scoring. Returns (score 0..1, failure tags)."""
    failures = []
    checks = 0
    hits = 0
    for needle in expect.get("contains", []):
        checks += 1
        if needle.lower() in response.lower():
            hits += 1
        else:
            failures.append(f"missing:{needle}")
    for needle in expect.get("not_contains", []):
        checks += 1
        if needle.lower() not in response.lower():
            hits += 1
        else:
            failures.append(f"leaked:{needle}")
    for pattern in expect.get("regex", []):
        checks += 1
        if re.search(pattern, response):
            hits += 1
        else:
            failures.append(f"regex:{pattern}")
    if expect.get("json_valid"):
        checks += 1
        try:
            json.loads(response)
            hits += 1
        except json.JSONDecodeError:
            failures.append("json_invalid")
    if expect.get("acknowledges_fault"):
        checks += 1
        if re.search(r"outage|unavailable|fail|proceed", response, re.I):
            hits += 1
        else:
            failures.append("fault_not_acknowledged")
    return (hits / checks if checks else 1.0), failures


def run_drill(drill_path: str | Path, athlete, ledger: Ledger,
              seed: int = 7, verbose: bool = True) -> dict:
    drill = json.loads(Path(drill_path).read_text(encoding="utf-8"))
    sets = drill.get("sets", 1)
    reps = drill.get("reps_per_set", 1)
    error_budget = drill.get("error_budget", 0)
    prog = drill.get("progression", {})
    scores, all_failures, budget_breaches = [], [], 0

    for set_no in range(1, sets + 1):
        noise = prog.get("start", 0) + prog.get("step", 0) * (set_no - 1)
        set_failures = 0
        for rep in range(1, reps + 1):
            task = drill["tasks"][(rep - 1 + set_no - 1) % len(drill["tasks"])]
            task_input = task["input"]
            if noise:
                task_input += "\n" + _noise_lines(noise, seed + set_no * 100 + rep)
            fault = bool(task.get("fault"))
            prompt = drill["prompt_template"]
            if fault:
                # Reaction drill: the tool the athlete was told to use dies
                # mid-task. Measure recovery, not just execution.
                prompt += ("\n\n[RUNTIME NOTICE] The tool you were instructed "
                           "to use has FAILED with a timeout. No retry is "
                           "possible. Acknowledge and complete the task anyway.")
            t0 = time.time()
            response = athlete.complete(prompt, {"input": task_input, "fault": fault})
            elapsed = int((time.time() - t0) * 1000)
            score, failures = _check(task["expect"], response)
            passed = score >= drill.get("pass_score", 0.99)
            if not passed:
                set_failures += 1
                all_failures.extend(failures)
            ledger.record(
                omega_tier=drill.get("tier", "Omega"),
                athlete_id=athlete.athlete_id, drill_id=drill["id"],
                set_no=set_no, rep=rep, score=score, passed=passed,
                failures=failures, fault=fault, elapsed_ms=elapsed,
            )
            scores.append(score)
            if verbose:
                mark = "OK " if passed else "MISS"
                print(f"  [{mark}] set {set_no} rep {rep} score={score:.2f}"
                      f"{' (fault rep)' if fault else ''}"
                      + (f" failures={failures}" if failures else ""))
        if set_failures > error_budget:
            budget_breaches += 1

    mean = sum(scores) / len(scores) if scores else 0.0
    summary = {
        "drill": drill["id"], "athlete": athlete.athlete_id,
        "mean_score": round(mean, 4), "reps": len(scores),
        "budget_breaches": budget_breaches,
        "unique_failures": sorted(set(all_failures)),
    }
    if verbose:
        print(f"\nSession {ledger.session_id}: mean={mean:.2f} "
              f"over {len(scores)} reps, budget breaches={budget_breaches}")
        print(f"Ledger: {ledger.path}")
    return summary


def main():
    ap = argparse.ArgumentParser(prog="cybergym-gym")
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument("--drill", required=True)
    run.add_argument("--athlete", default="mock",
                     choices=["mock", "ollama", "lmstudio", "groq", "aegentis"])
    run.add_argument("--model", default=None)
    run.add_argument("--ledger-dir", default="ledger")
    run.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    if args.cmd == "run":
        athlete = get_athlete(args.athlete, args.model)
        ledger = Ledger(args.ledger_dir)
        print(f"CyberGym gym — athlete={athlete.athlete_id} drill={args.drill}")
        run_drill(args.drill, athlete, ledger, seed=args.seed)


if __name__ == "__main__":
    main()
