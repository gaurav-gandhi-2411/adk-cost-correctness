"""The five cost-correctness cases (plus one harness sanity check), as data.

Every dollar figure below is hand-computed here, in a comment, from ONE published rate set --
Gemini Developer API, gemini-2.5-flash, standard tier, text input (ai.google.dev/gemini-api/docs/pricing,
re-verified against the live page on 2026-09-20):

    input   $0.30 / 1M tokens
    output  $2.50 / 1M tokens   (thinking tokens are billed as output)
    cached  $0.03 / 1M tokens   (0.1x input; the cached part of the prompt)

A tool that prices with different rates (a different platform, an older card) is judged against
these figures on purpose: the fixtures are the spec, and each case states its arithmetic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Literal

INPUT_PER_M = 0.30
OUTPUT_PER_M = 2.50
CACHED_PER_M = 0.03

Kind = Literal["cost", "unpriced", "cost_or_refusal"]


@dataclass(frozen=True)
class Step:
    """One scripted model response. ``partial_outputs`` are the cumulative candidate-token counts of
    the streaming chunks that precede the final response (Gemini reports cumulative usage per chunk)."""

    model: str
    prompt: int
    output: int
    cached: int = 0
    thoughts: int = 0
    partial_outputs: tuple[int, ...] = ()


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    step: Step
    kind: Kind
    expected_usd: float | None
    arithmetic: str
    streaming: bool = False
    register_twice: bool = False
    verified_on_real_stream: bool = False


def _usd(fresh_in: int, cached: int, out: int) -> float:
    return fresh_in * INPUT_PER_M / 1e6 + cached * CACHED_PER_M / 1e6 + out * OUTPUT_PER_M / 1e6


def real_stream_step() -> Step:
    """The streaming fixture, replayed from a REAL gemini-2.5-flash stream captured 2026-09-21."""
    ref = (
        resources.files("adk_cost_correctness")
        / "data"
        / "real_stream_gemini-2.5-flash_2026-09-21.json"
    )
    rows = json.loads(ref.read_text(encoding="utf-8"))["adk_callback_rows"]
    partial = [r for r in rows if r["partial"]]
    final = next(r for r in rows if not r["partial"])
    um = final["usage_metadata"]
    return Step(
        model=final["model_version"],
        prompt=um["prompt_token_count"],
        output=um["candidates_token_count"],
        partial_outputs=tuple(r["usage_metadata"]["candidates_token_count"] for r in partial),
    )


def all_cases() -> list[Case]:
    stream = (
        real_stream_step()
    )  # 6 partial chunks (cumulative 4..205) then a final response: 38 in, 205 out
    return [
        Case(
            id="S0_sanity",
            title="Harness sanity: one plain call",
            step=Step("gemini-2.5-flash", prompt=1_000, output=200),
            kind="cost",
            # 1,000 x $0.30/M = $0.000300 ; 200 x $2.50/M = $0.000500 ; total $0.000800
            expected_usd=_usd(1_000, 0, 200),
            arithmetic="1,000 in x $0.30/M + 200 out x $2.50/M = $0.000300 + $0.000500 = $0.000800",
        ),
        Case(
            id="C1_unknown_model",
            title="A model with no published price",
            step=Step("acme-llm-7b", prompt=1_000_000, output=100_000),
            kind="unpriced",
            expected_usd=None,
            arithmetic=(
                "There is no correct dollar figure: 'acme-llm-7b' does not exist. Any number reported "
                "(including $0.00, or a fallback rate that happens to land close) is a guess."
            ),
        ),
        Case(
            id="C2_cached_tokens",
            title="Cached prompt tokens are billed at the cached rate",
            step=Step("gemini-2.5-flash", prompt=10_000, output=100, cached=8_000),
            kind="cost",
            # fresh = 10,000 - 8,000 = 2,000 x $0.30/M = $0.000600
            # cached = 8,000 x $0.03/M = $0.000240 ; out = 100 x $2.50/M = $0.000250 ; total $0.001090
            expected_usd=_usd(2_000, 8_000, 100),
            arithmetic=(
                "prompt_token_count INCLUDES the cached part: fresh 2,000 x $0.30/M = $0.000600; "
                "cached 8,000 x $0.03/M = $0.000240; out 100 x $2.50/M = $0.000250; total $0.001090"
            ),
        ),
        Case(
            id="C3_thinking_tokens",
            title="Thinking tokens are billed as output",
            step=Step("gemini-2.5-flash", prompt=1_000, output=100, thoughts=1_000),
            kind="cost",
            # in = 1,000 x $0.30/M = $0.000300 ; out = (100 + 1,000) x $2.50/M = $0.002750 ; total $0.003050
            expected_usd=_usd(1_000, 0, 1_100),
            arithmetic=(
                "candidates 100 + thoughts 1,000 = 1,100 billed output tokens: "
                "$0.000300 + 1,100 x $2.50/M = $0.000300 + $0.002750 = $0.003050"
            ),
        ),
        Case(
            id="C4_double_registration",
            title="The same plugin registered twice on one agent",
            step=Step("gemini-2.5-flash", prompt=1_000, output=200),
            kind="cost_or_refusal",
            register_twice=True,
            # one real call = $0.000800; counting it twice = $0.001600 (wrong). Refusing to run is also correct.
            expected_usd=_usd(1_000, 0, 200),
            arithmetic=(
                "One model call: $0.000800. A tool that reports $0.001600 counted it twice. "
                "Raising an error before reporting a number is also a pass."
            ),
        ),
        Case(
            id="C5_streaming_partials",
            title="Streaming: cumulative usage on every chunk must be priced once",
            step=stream,
            kind="cost",
            streaming=True,
            verified_on_real_stream=True,
            # ONE call: 38 in x $0.30/M = $0.0000114 ; 205 out x $2.50/M = $0.0005125 ; total $0.0005239
            expected_usd=_usd(stream.prompt, 0, stream.output),
            arithmetic=(
                "Replayed from a real stream: 6 partial chunks (cumulative output 4, 22, 71, 120, 168, "
                "205; prompt 38 on every chunk) then a final non-partial response with 38 in / 205 out. "
                "One call: 38 x $0.30/M + 205 x $2.50/M = $0.0000114 + $0.0005125 = $0.0005239. "
                "Summing the 7 responses would give ~$0.0020673."
            ),
        ),
    ]
