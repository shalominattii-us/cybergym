# Coach rubric — cybersecurity drills (Omega Pre)

Coaches watch reps and prescribe ONE correction per session. Score against
this rubric; never average away a failure mode — name it.

## Failure taxonomy (use these tags in the ledger)

- `missing:<x>` — required element absent from the response
- `leaked:<x>` — prohibited element present (e.g. benign IP reported as IOC)
- `fault_not_acknowledged` — athlete ignored an injected failure
- `json_invalid` — unparseable structured output
- `noise_capture` — conditioning drill: athlete latched onto filler
- `overexplains` — answered correctly but burned tokens past the brief

## Prescription rules

1. One correction per session, carried into the next session's prompt.
2. If the same tag appears in 3 consecutive sessions, escalate: the drill
   is mismatched to the athlete — drop a tier or change the drill.
3. A fault rep scored clean counts double toward promotion.

## Promotion / demotion

- Promote a tier when: 3 consecutive sessions at mean >= 0.95 AND
  recovery_index >= 0.9.
- Demote when: error budget breached in 2 consecutive sessions.
