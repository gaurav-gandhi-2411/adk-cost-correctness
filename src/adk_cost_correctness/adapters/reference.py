"""A cost plugin that gets every case right (the executable spec), and a naive one that gets them
wrong the way real tools do. The tests prove the suite passes the first and fails the second, so a
scorecard cannot be an artefact of a badly written fixture, and the suite is satisfiable by code that
is not one of the tools it scores.

``ReferencePlugin`` prices from the SAME published rates the cases are written from (``cases.RATES``)
plus the grounding rules; a model it has no rate for is reported unknown, never guessed.
"""

from __future__ import annotations

from typing import Any

from google.adk.plugins import BasePlugin

from ..cases import (
    GROUNDING_PER_PROMPT_GEMINI_2_5,
    GROUNDING_PER_QUERY_GEMINI_3,
    INPUT_PER_M,
    OUTPUT_PER_M,
    RATES,
    Case,
)
from ..scoring import Outcome
from .base import RunContext


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
        if model not in RATES:
            self.unknown.append(model)  # never guess
            return
        rin, rout, rcache, raudio = RATES[model]
        u = llm_response.usage_metadata
        cached = u.cached_content_token_count or 0
        audio = 0
        for d in u.prompt_tokens_details or []:
            if str(getattr(d.modality, "value", d.modality)) == "AUDIO":
                audio += d.token_count or 0
        text_in = (u.prompt_token_count or 0) - cached - audio
        out = (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
        tool_use = u.tool_use_prompt_token_count or 0  # billed as input tokens
        self.total += (text_in + tool_use) * rin / 1e6 + cached * rcache / 1e6 + out * rout / 1e6
        if audio and raudio is not None:
            self.total += audio * raudio / 1e6
        queries = len(getattr(llm_response.grounding_metadata, "web_search_queries", None) or [])
        if queries:
            # Gemini 2.5: one charge per grounded prompt; Gemini 3.x: per search request
            self.total += (
                queries * GROUNDING_PER_QUERY_GEMINI_3
                if model.startswith("gemini-3")
                else GROUNDING_PER_PROMPT_GEMINI_2_5
            )


class NaivePlugin(BasePlugin):
    """Guesses an unknown model at a fallback rate, prices every response it is handed (partials and
    duplicates included), bills cached tokens as fresh input, and ignores thinking tokens, tool-use
    tokens, audio and grounding."""

    def __init__(self) -> None:
        super().__init__(name="naive_cost")
        self.total = 0.0

    async def after_model_callback(self, *, callback_context: Any, llm_response: Any) -> None:
        u = llm_response.usage_metadata
        if u is None:
            return
        rin, rout, _, _ = RATES.get(
            llm_response.model_version or "", (INPUT_PER_M, OUTPUT_PER_M, 0, None)
        )
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
