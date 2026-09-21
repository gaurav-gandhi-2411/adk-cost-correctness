"""A minimal cost plugin that gets all five cases right, and a naive one that gets them wrong the
way real tools do. They are the executable spec: the test-suite proves the suite passes the first
and fails the second, so a scorecard cannot be an artefact of a badly written fixture.

``ReferencePlugin`` is ~40 lines on purpose: correct behaviour here is not hard, it is just easy to skip.
"""

from __future__ import annotations

from typing import Any

from google.adk.plugins import BasePlugin

from ..cases import CACHED_PER_M, INPUT_PER_M, OUTPUT_PER_M, Case
from ..scoring import Outcome
from .base import RunContext

_RATES = {"gemini-2.5-flash": (INPUT_PER_M, OUTPUT_PER_M, CACHED_PER_M)}


class ReferencePlugin(BasePlugin):
    def __init__(self) -> None:
        super().__init__(name="reference_cost")
        self.total = 0.0
        self.unknown: list[str] = []
        self._seen: set[int] = set()

    async def after_model_callback(self, *, callback_context: Any, llm_response: Any) -> None:
        if llm_response.partial or llm_response.usage_metadata is None:
            return  # a partial chunk repeats usage the final response reports; price the final one
        if id(llm_response) in self._seen:
            raise RuntimeError("registered twice: this response was already counted")
        self._seen.add(id(llm_response))
        model = llm_response.model_version or ""
        if model not in _RATES:
            self.unknown.append(model)  # never guess
            return
        rin, rout, rcache = _RATES[model]
        u = llm_response.usage_metadata
        cached = u.cached_content_token_count or 0
        out = (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
        self.total += ((u.prompt_token_count or 0) - cached) * rin / 1e6
        self.total += cached * rcache / 1e6 + out * rout / 1e6


class NaivePlugin(BasePlugin):
    """Guesses an unknown model at a fallback rate, prices every response it is handed (partials and
    duplicates included), and does not add cached tokens back at the cached rate."""

    def __init__(self) -> None:
        super().__init__(name="naive_cost")
        self.total = 0.0

    async def after_model_callback(self, *, callback_context: Any, llm_response: Any) -> None:
        u = llm_response.usage_metadata
        if u is None:
            return
        rin, rout, _ = _RATES.get(llm_response.model_version or "", (INPUT_PER_M, OUTPUT_PER_M, 0))
        self.total += (u.prompt_token_count or 0) * rin / 1e6 + (
            u.candidates_token_count or 0
        ) * rout / 1e6


class _Base:
    plugin: Any

    def version(self) -> str:
        return "in-repo"

    def plugins(self) -> list[Any]:
        return [self.plugin]

    def agent_kwargs(self) -> dict[str, Any]:
        return {"after_model_callback": self.plugin.after_model_callback}


class ReferenceAdapter(_Base):
    name = "reference (in-repo, correct)"

    def start(self, case: Case) -> None:
        self.plugin = ReferencePlugin()

    def collect(self, ctx: RunContext) -> Outcome:
        if self.plugin.unknown and not self.plugin.total:
            return Outcome(total_usd=None, flagged=True)
        return Outcome(total_usd=self.plugin.total)


class NaiveAdapter(_Base):
    name = "naive (in-repo, wrong on purpose)"

    def start(self, case: Case) -> None:
        self.plugin = NaivePlugin()

    def collect(self, ctx: RunContext) -> Outcome:
        return Outcome(total_usd=self.plugin.total)
