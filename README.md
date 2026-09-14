# CyberGym — The AI Agent Gym

**Status: Omega Pre — drill engine + ledger live, sparring and genetic layers staged.**

Benchmarks are weigh-ins. A gym is what happens *between* them. Agents here
don't get scored once — they train, fatigue, adapt, plateau, recover, and
peak. The gym is judged on **rate of improvement**, not static performance.

## The training floor

| Modality | What it builds | First drill |
|---|---|---|
| Drills (skill isolation) | Reps, sets, progression curves per capability | `drills/precision/log_triage_01.json` |
| Conditioning (endurance) | Long-context stamina, degraded-state work | `drills/conditioning/ctx_stamina_01.json` |
| Reaction (surprise) | Recovery from mid-task failures | `drills/reaction/tool_outage_01.json` |
| Sparring (Omega Omega) | Matched agent-vs-agent adversarial practice | staged — see `sparring/` |
| Film & coach (Omega Omega Omega) | Replay, failure taxonomy, one correction forward | staged — see `film/` |

## Quickstart (zero dependencies, Python 3.11+)

```bash
# Smoke run with the built-in mock athlete
python -m gym.engine run --drill drills/precision/log_triage_01.json --athlete mock

# Real athlete on the local LLM Armada (Ollama :11434)
python -m gym.engine run --drill drills/conditioning/ctx_stamina_01.json --athlete ollama --model llama3.1:8b

# Or LM Studio (auto-detects whatever model is loaded, incl. Heretic builds)
python -m gym.engine run --drill drills/precision/log_triage_01.json --athlete lmstudio

# Cloud bridge athlete (Groq) — key from env, never from a file
export GROQ_API_KEY=...   # placeholder only; real key lives in the vault
python -m gym.engine run --drill drills/reaction/tool_outage_01.json --athlete groq

# Front desk: what should this athlete train next?
python -m gym.scheduler --ledger-dir ledger --athlete mock --drills-dir drills

# Scoreboard: improvement velocity, recovery index, failure half-life
python -m gym.scoring --ledger-dir ledger --athlete mock
```

Windows unit (GPO-locked): use the established IEX pattern —

```powershell
powershell -ep bypass -c "iex (gc "$env:USERPROFILE\CyberGym\scripts\Start-GymSession.ps1" -raw)"
```

## Metrics — what "fit" means

- **Improvement velocity** — slope of session means over time
- **Failure half-life** — sessions until a coached weakness reappears
- **Recovery index** — fault-rep score as a fraction of clean-rep score
- **Stamina curve** — score vs. position within a session
- **Spar record** — (Omega Omega) win/loss across matched opponents

## Architecture

```
gym/engine.py     drill engine: sets x reps, deterministic checks, fault injection
gym/athlete.py    Athlete protocol + Mock/Ollama/Groq/Aegentix adapters
gym/ledger.py     append-only JSONL, Omega-tiered, every rep preserved
gym/scoring.py    improvement velocity, recovery index, failure half-life
gym/scheduler.py  front desk — prescribes the next workout from the ledger
drills/           drill definitions (JSON): precision / conditioning / reaction
coaches/rubrics/  failure taxonomy + promotion/demotion rules
sparring/         Omega Omega — staged
film/             Omega Omega Omega — staged (genetic jam layer behind it)
scripts/          Start-GymSession.ps1 (A2D standard)
tests/            smoke test — MockAthlete genuinely solves the IOC drills
```

## Design decisions (v0.1)

1. **First athlete: the generic harness.** AEGENTIS plugs in as an adapter
   (`AegentixAthlete`), because the gym must outlive any one athlete — and
   matched sparring needs multiple athletes by definition.
2. **First drill set: cybersecurity-flavored.** Aligns with Eagle Shield and
   the defense corpus (SOC triage, long-watch stamina, promptware-era tool
   failure recovery).

## Build order

- [x] **Omega Pre** — drill engine + ledger + one drill per modality
- [ ] **Omega Omega** — sparring engine, matched-pair scheduler
- [ ] **Omega Omega Omega** — film/coach layer, then the genetic jam
