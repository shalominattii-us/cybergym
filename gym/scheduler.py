"""Front desk — routes athletes to today's workout from yesterday's film.

Omega Pre version: prescribe the modality with the weakest recent mean.
Sparring-aware scheduling lands at Omega Omega with the sparring engine.

Usage:
    python -m gym.scheduler --ledger-dir ledger --athlete mock --drills-dir drills
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ledger import read_all


def modality_means(entries: list[dict], athlete_id: str,
                   drills: dict[str, str]) -> dict[str, float]:
    acc: dict[str, list[float]] = {}
    for e in entries:
        if e["athlete_id"] != athlete_id:
            continue
        modality = drills.get(e["drill_id"], "unknown")
        acc.setdefault(modality, []).append(e["score"])
    return {m: sum(s) / len(s) for m, s in acc.items()}


def load_catalog(drills_dir: str | Path) -> dict[str, str]:
    """drill_id -> modality, from every drill definition on the floor."""
    catalog = {}
    for path in Path(drills_dir).rglob("*.json"):
        drill = json.loads(path.read_text(encoding="utf-8"))
        catalog[drill["id"]] = drill.get("modality", "unknown")
    return catalog


def prescribe(ledger_dir: str, athlete_id: str, drills_dir: str) -> dict:
    entries = read_all(ledger_dir)
    catalog = load_catalog(drills_dir)
    means = modality_means(entries, athlete_id, catalog)
    trained = set(means)
    untrained = [d for d, m in catalog.items() if m not in trained]
    if untrained:
        return {"athlete": athlete_id, "reason": "new modality on the floor",
                "next_drill": untrained[0]}
    if not means:
        first = next(iter(catalog), None)
        return {"athlete": athlete_id, "reason": "intake — baseline first",
                "next_drill": first}
    weakest = min(means, key=means.get)
    candidates = [d for d, m in catalog.items() if m == weakest]
    return {"athlete": athlete_id,
            "reason": f"weakest modality: {weakest} (mean {means[weakest]:.2f})",
            "next_drill": candidates[0] if candidates else None}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger-dir", default="ledger")
    ap.add_argument("--athlete", required=True)
    ap.add_argument("--drills-dir", default="drills")
    args = ap.parse_args()
    print(json.dumps(prescribe(args.ledger_dir, args.athlete, args.drills_dir),
                     indent=2))
