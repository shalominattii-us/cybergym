# Sparring engine — Omega Omega (staged, not built)

Live adversarial practice. Lands after the drill engine proves out.

## Design contract

- Matched pairs only — mismatches teach nobody. Tiers come from the
  ledger: improvement velocity + spar record by domain.
- One attacker, one defender, then swap. Attacker injects confusion,
  exploits overconfidence, probes failure modes the ledger already knows.
- Red-cell corner: a dedicated adversary whose only job is finding the
  other athlete's failure modes.
- Every spar produces a film session: replay + failure taxonomy +
  one coached correction (feeds `coaches/rubrics/`).

## Interface it must satisfy

```python
class Spar(Protocol):
    def run(self, red: Athlete, blue: Athlete, scenario: dict) -> SparResult: ...
```

`SparResult` writes to the same ledger as drills — sparring is just a
drill whose grader is another athlete.
