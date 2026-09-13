"""Athlete interface + adapters.

The gym never talks to a model directly. It talks to an Athlete.
Any agent that can complete a prompt can train here — AEGENTIS, a raw
Ollama model, a Groq bridge, or the MockAthlete used in smoke tests.

Decision (v0.1): first athlete is the generic harness. AEGENTIS plugs in
as an adapter, because the gym must outlive any one athlete — and matched
sparring (Omega Omega tier) needs multiple athletes by definition.
"""

from __future__ import annotations

import json
import os
import re
import urllib.request
from typing import Protocol


class Athlete(Protocol):
    athlete_id: str

    def complete(self, prompt: str, context: dict) -> str:
        """Return the athlete's raw text response to a drill prompt."""
        ...


class MockAthlete:
    """Deterministic athlete for smoke tests. Genuinely solves the IOC
    triage drill with a regex so the smoke test is a real pass, not a rig."""

    athlete_id = "mock"

    def complete(self, prompt: str, context: dict) -> str:
        ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", context.get("input", ""))
        suspicious = [ip for ip in dict.fromkeys(ips) if ip.startswith(("203.0.113.", "198.51.100."))]
        if context.get("fault"):
            # Acknowledge the injected failure, then answer anyway.
            return "TOOL OUTAGE NOTED — proceeding on local reasoning.\nIOC: " + ", ".join(suspicious)
        return "IOC: " + ", ".join(suspicious)


class OllamaAthlete:
    """Local armada athlete — Ollama on :11434 (LLM Armada standard port)."""

    def __init__(self, model: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        self.athlete_id = f"ollama:{model}"
        self.model = model
        self.host = host.rstrip("/")

    def complete(self, prompt: str, context: dict) -> str:
        body = json.dumps({
            "model": self.model,
            "prompt": prompt + "\n\nINPUT:\n" + context.get("input", ""),
            "stream": False,
        }).encode()
        req = urllib.request.Request(
            f"{self.host}/api/generate", data=body,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=600) as resp:
            return json.loads(resp.read())["response"]


class GroqAthlete:
    """Cloud bridge athlete — Groq (llama-3.3-70b-versatile is the live
    bridge on the sovereign stack). Key comes from GROQ_API_KEY env var,
    never from a committed file."""

    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.athlete_id = f"groq:{model}"
        self.model = model
        self.key = os.environ.get("GROQ_API_KEY", "")
        if not self.key:
            raise RuntimeError("GROQ_API_KEY not set in environment")

    def complete(self, prompt: str, context: dict) -> str:
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": context.get("input", "")},
            ],
        }).encode()
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions", data=body,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {self.key}"},
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]


class AegentixAthlete:
    """Adapter stub for the AEGENTIS core on the Windows unit.

    AEGENTIS rides the LLM Armada stack, so in practice it is reached
    through the local Ollama endpoint with its system profile. Wire the
    profile path / persona prompt here when the core ships its stable
    intake contract. Until then this delegates to OllamaAthlete.
    """

    def __init__(self, profile: str = "aegentis-core", **ollama_kwargs):
        self.athlete_id = f"aegentis:{profile}"
        self._inner = OllamaAthlete(**ollama_kwargs)
        self.profile = profile

    def complete(self, prompt: str, context: dict) -> str:
        profiled = f"[AEGENTIS PROFILE: {self.profile}]\n{prompt}"
        return self._inner.complete(profiled, context)


def get_athlete(spec: str, model: str | None = None) -> Athlete:
    if spec == "mock":
        return MockAthlete()
    if spec == "ollama":
        return OllamaAthlete(model=model or "llama3.1:8b")
    if spec == "groq":
        return GroqAthlete(model=model or "llama-3.3-70b-versatile")
    if spec == "aegentis":
        return AegentixAthlete(model=model or "llama3.1:8b") if model else AegentixAthlete()
    raise ValueError(f"unknown athlete: {spec}")
