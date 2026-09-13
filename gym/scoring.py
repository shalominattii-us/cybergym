"""Gym metrics — what "fit" means.

Not raw accuracy. The scoreboard tracks:
- improvement velocity: slope of session mean scores over time
- failure half-life: sessions until a known failure tag stops reappearing
- recovery index: fault-rep score as a fraction of clean-rep score
- stamina curve: score vs. position within a session
"""

from __future__ import annotations

from .ledger import read_all


def _sessions(entries: list[dict], athlete_id: str) -> dict[str, list[dict]]:
    by: dict[str, list[dict]] = {}
    for e in entries:
        if e["athlete_id"] == athlete_id:
            by.setdefault(e["session_id"], []).append(e)
    return dict(sorted(by.items()))


def session_means(entries: list[dict], athlete_id: str) -> list[float]:
    means = []
    for sess in _sessions(entries, athlete_id).values():
        means.append(sum(e["score"] for e in sess) / len(sess))
    return means


def improvement_velocity(entries: list[dict], athlete_id: str) -> float:
    """Least-squares slope of session means. Positive = getting fitter."""
    ys = session_means(entries, athlete_id)
    n = len(ys)
    if n < 2:
        return 0.0
    xs = list(range(n))
    xbar, ybar = sum(xs) / n, sum(ys) / n
    denom = sum((x - xbar) ** 2 for x in xs)
    return sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / denom if denom else 0.0


def recovery_index(entries: list[dict], athlete_id: str) -> float:
    """Fault-rep performance relative to clean reps. 1.0 = unshaken."""
    fault, clean = [], []
    for e in entries:
        if e["athlete_id"] != athlete_id:
            continue
        (fault if e.get("fault") else clean).append(e["score"])
    if not fault or not clean:
        return 1.0
    clean_mean = sum(clean) / len(clean)
    return round((sum(fault) / len(fault)) / clean_mean, 4) if clean_mean else 0.0


def failure_half_life(entries: list[dict], athlete_id: str) -> dict[str, int]:
    """Per failure tag: sessions since first seen until it stopped appearing.
    A tag that never reappears after session k has half-life k."""
    sess = _sessions(entries, athlete_id)
    first: dict[str, int] = {}
    last: dict[str, int] = {}
    for i, entries_in in enumerate(sess.values()):
        tags = {f for e in entries_in for f in e.get("failures", [])}
        for t in tags:
            first.setdefault(t, i)
            last[t] = i
    return {t: last[t] - first[t] for t in first}


def report(ledger_dir: str, athlete_id: str) -> dict:
    entries = read_all(ledger_dir)
    return {
        "athlete": athlete_id,
        "sessions": len(_sessions(entries, athlete_id)),
        "session_means": [round(m, 4) for m in session_means(entries, athlete_id)],
        "improvement_velocity": round(improvement_velocity(entries, athlete_id), 4),
        "recovery_index": recovery_index(entries, athlete_id),
        "failure_half_life": failure_half_life(entries, athlete_id),
    }


if __name__ == "__main__":
    import argparse
    import json

    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger-dir", default="ledger")
    ap.add_argument("--athlete", required=True)
    args = ap.parse_args()
    print(json.dumps(report(args.ledger_dir, args.athlete), indent=2))
