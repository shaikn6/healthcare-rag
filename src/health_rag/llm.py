"""LLM interface: Claude impl + Fake for tests."""
from __future__ import annotations
import os
from typing import Protocol

MODEL = "claude-sonnet-4-6"


class LLM(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class ClaudeLLM:
    def __init__(self, model: str = MODEL):
        from anthropic import Anthropic
        self._c = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._m = model

    def complete(self, system: str, user: str) -> str:
        msg = self._c.messages.create(
            model=self._m, max_tokens=1024, system=system,
            messages=[{"role": "user", "content": user}],
        )
        return msg.content[0].text


class FakeLLM:
    def complete(self, system: str, user: str) -> str:
        return "[fake clinical answer grounded on retrieved guideline context]"
