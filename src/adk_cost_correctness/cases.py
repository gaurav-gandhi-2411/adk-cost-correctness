"""The cost-correctness cases, as data.

Every dollar figure is hand-computed in a comment next to the case, from published vendor prices that
were read from the vendor's own page on the date in ``sources``. The suite has two groups:

* ``origin="original"`` (C1-C5, added 2026-09-21): the first five, chosen AFTER a hands-on comparison had
  shown where one of the two scored tools fell short, so they are biased toward the other tool.
* ``origin="counter"`` (G*, T1, A1, M*; added 2026-09-21, after the original five): counter-cases drawn from
  what the other tool does that the author's tool does not (grounding fees, other vendors' models) and from
  ADK features neither handles (audio input, tool-use prompt tokens). Their results were not known when
  they were written and none was changed afterwards.

Prices (USD per 1M tokens unless noted), all read on 2026-09-21:

  gemini-2.5-flash  in 0.30 | out 2.50 | cached 0.03 | audio in 1.00      ai.google.dev/gemini-api/docs/pricing
  gemini-3.5-flash  in 1.50 | out 9.00                                     ai.google.dev/gemini-api/docs/pricing
  gpt-4o            in 2.50 | out 10.00                                    developers.openai.com/api/docs/pricing.md
  claude-opus-5     in 5.00 | out 25.00                                    platform.claude.com/docs/en/about-claude/pricing.md
  Google Search grounding, Gemini 2.5:  $35 / 1,000 grounded prompts (one charge however many queries)
  Google Search grounding, Gemini 3.x:  $14 / 1,000 search requests (per query), Gemini API and Vertex AI pages
  Tool-use prompt tokens (URL context): counted as input tokens; ai.google.dev/gemini-api/docs/url-context

Grounding fees apply beyond a free allowance (Gemini 2.5: 1,500 prompts/day; Gemini 3.x: 5,000 requests/month).
A plugin cannot see an account's remaining allowance, so the grounding cases price a request PAST the free
allowance, at the published paid rate, and say so.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from typing import Literal

Kind = Literal["cost", "unpriced", "cost_or_refusal"]
Origin = Literal["original", "counter"]

# model -> (input, output, cached, audio input or None if not used by a case), USD per 1M tokens
RATES: dict[str, tuple[float, float, float, float | None]] = {
    "gemini-2.5-flash": (0.30, 2.50, 0.03, 1.00),
    "gemini-3.5-flash": (1.50, 9.00, 0.15, None),
    "gpt-4o": (2.50, 10.00, 1.25, None),
    "claude-opus-5": (5.00, 25.00, 0.50, None),
}
GROUNDING_PER_PROMPT_GEMINI_2_5 = 35 / 1000  # $0.035 per grounded prompt
GROUNDING_PER_QUERY_GEMINI_3 = 14 / 1000  # $0.014 per search request

# kept for the reference plugin
INPUT_PER_M, OUTPUT_PER_M, CACHED_PER_M, _ = RATES["gemini-2.5-flash"]


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
    tool_use_prompt: int = 0  # tokens fetched by a built-in tool (URL context), billed as input
    audio_prompt: int = 0  # audio tokens INSIDE prompt_token_count
    grounding_queries: int = 0  # web_search_queries on the response's grounding_metadata
    calls_tool: str = ""  # a function_call to this tool instead of text


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    step: Step
    kind: Kind
    expected_usd: float | None
    arithmetic: str
    origin: Origin = "original"
    added_on: str = "2026-09-21"
    sources: tuple[str, ...] = ()
    # Figures that mean "priced, but a component the vendor publishes a price for was left out".
    incomplete_usd: tuple[float, ...] = ()
    streaming: bool = False
    register_twice: bool = False
    verified_on_real_stream: bool = False
    builtin_google_search: bool = False  # agent carries ADK's real google_search tool
    google_search_agent_tool: bool = (
        False  # root calls ADK's GoogleSearchAgentTool; sub_step is its call
    )
    sub_step: Step | None = None
    followup_step: Step | None = None  # the root's next call after a tool call (G3)


def _usd(model: str, fresh_in: int, cached: int, out: int, audio: int = 0) -> float:
    rin, rout, rcache, raudio = RATES[model]
    if audio and raudio is None:
        raise ValueError(f"no published audio rate recorded for {model}")
    return (fresh_in * rin + cached * rcache + out * rout + audio * (raudio or 0.0)) / 1e6


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


GEMINI_PAGE = "ai.google.dev/gemini-api/docs/pricing (read 2026-09-21)"
VERTEX_PAGE = "cloud.google.com/vertex-ai/generative-ai/pricing (read 2026-09-21)"


def all_cases() -> list[Case]:
    stream = (
        real_stream_step()
    )  # 6 partial chunks (cumulative 4..205) then a final response: 38 in, 205 out
    f = "gemini-2.5-flash"
    g3 = "gemini-3.5-flash"
    return [
        Case(
            id="S0_sanity",
            title="Harness sanity: one plain call",
            step=Step(f, prompt=1_000, output=200),
            kind="cost",
            # 1,000 x $0.30/M = $0.000300 ; 200 x $2.50/M = $0.000500 ; total $0.000800
            expected_usd=_usd(f, 1_000, 0, 200),
            arithmetic="1,000 in x $0.30/M + 200 out x $2.50/M = $0.000300 + $0.000500 = $0.000800",
            sources=(GEMINI_PAGE,),
        ),
        # ---- original five: chosen post hoc (see module docstring) --------------------------------
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
            step=Step(f, prompt=10_000, output=100, cached=8_000),
            kind="cost",
            # fresh = 10,000 - 8,000 = 2,000 x $0.30/M = $0.000600
            # cached = 8,000 x $0.03/M = $0.000240 ; out = 100 x $2.50/M = $0.000250 ; total $0.001090
            expected_usd=_usd(f, 2_000, 8_000, 100),
            # cached tokens left out entirely: $0.000600 + $0.000250 = $0.000850
            incomplete_usd=(_usd(f, 2_000, 0, 100),),
            arithmetic=(
                "prompt_token_count INCLUDES the cached part: fresh 2,000 x $0.30/M = $0.000600; "
                "cached 8,000 x $0.03/M = $0.000240; out 100 x $2.50/M = $0.000250; total $0.001090"
            ),
            sources=(GEMINI_PAGE,),
        ),
        Case(
            id="C3_thinking_tokens",
            title="Thinking tokens are billed as output",
            step=Step(f, prompt=1_000, output=100, thoughts=1_000),
            kind="cost",
            # in = 1,000 x $0.30/M = $0.000300 ; out = (100 + 1,000) x $2.50/M = $0.002750 ; total $0.003050
            expected_usd=_usd(f, 1_000, 0, 1_100),
            # thinking tokens dropped: $0.000300 + 100 x $2.50/M = $0.000550
            incomplete_usd=(_usd(f, 1_000, 0, 100),),
            arithmetic=(
                "candidates 100 + thoughts 1,000 = 1,100 billed output tokens: "
                "$0.000300 + 1,100 x $2.50/M = $0.000300 + $0.002750 = $0.003050"
            ),
            sources=(GEMINI_PAGE,),
        ),
        Case(
            id="C4_double_registration",
            title="The same plugin registered twice on one agent",
            step=Step(f, prompt=1_000, output=200),
            kind="cost_or_refusal",
            register_twice=True,
            # one real call = $0.000800; counting it twice = $0.001600 (wrong). Refusing to run is also correct.
            expected_usd=_usd(f, 1_000, 0, 200),
            arithmetic=(
                "One model call: $0.000800. A tool that reports $0.001600 counted it twice. "
                "Raising an error before reporting a number is also a pass."
            ),
            sources=(GEMINI_PAGE,),
        ),
        Case(
            id="C5_streaming_partials",
            title="Streaming: cumulative usage on every chunk must be priced once",
            step=stream,
            kind="cost",
            streaming=True,
            verified_on_real_stream=True,
            # ONE call: 38 in x $0.30/M = $0.0000114 ; 205 out x $2.50/M = $0.0005125 ; total $0.0005239
            expected_usd=_usd(f, stream.prompt, 0, stream.output),
            arithmetic=(
                "Replayed from a real stream: 6 partial chunks (cumulative output 4, 22, 71, 120, 168, "
                "205; prompt 38 on every chunk) then a final non-partial response with 38 in / 205 out. "
                "One call: 38 x $0.30/M + 205 x $2.50/M = $0.0000114 + $0.0005125 = $0.0005239. "
                "Summing the 7 responses would give ~$0.0020673."
            ),
            sources=(GEMINI_PAGE,),
        ),
        # ---- counter-cases, added after the original five (see module docstring) -----------------
        Case(
            id="G1_grounding_gemini_2_5",
            title="Google Search grounding on Gemini 2.5: one grounded prompt, three queries",
            step=Step(f, prompt=2_000, output=300, grounding_queries=3),
            kind="cost",
            origin="counter",
            builtin_google_search=True,
            # tokens: 2,000 x $0.30/M = $0.000600 ; 300 x $2.50/M = $0.000750 -> $0.001350
            # grounding: ONE grounded prompt = $35/1,000 = $0.035000 (three queries, still one charge)
            # total $0.036350 ; fee left out: $0.001350
            expected_usd=_usd(f, 2_000, 0, 300) + GROUNDING_PER_PROMPT_GEMINI_2_5,
            incomplete_usd=(_usd(f, 2_000, 0, 300),),
            arithmetic=(
                "tokens $0.000600 + $0.000750 = $0.001350; grounding is billed per GROUNDED PROMPT on Gemini "
                "2.5 ($35/1,000 = $0.035, one charge however many queries, priced past the free allowance); "
                "total $0.036350. ADK's real built-in google_search tool runs inside the model."
            ),
            sources=(GEMINI_PAGE, VERTEX_PAGE),
        ),
        Case(
            id="G2_grounding_gemini_3",
            title="Google Search grounding on Gemini 3.x: three queries, billed per query",
            step=Step(g3, prompt=2_000, output=300, grounding_queries=3),
            kind="cost",
            origin="counter",
            builtin_google_search=True,
            # tokens: 2,000 x $1.50/M = $0.003000 ; 300 x $9.00/M = $0.002700 -> $0.005700
            # grounding: 3 queries x $14/1,000 = $0.042000 ; total $0.047700 ; fee left out: $0.005700
            expected_usd=_usd(g3, 2_000, 0, 300) + 3 * GROUNDING_PER_QUERY_GEMINI_3,
            incomplete_usd=(_usd(g3, 2_000, 0, 300),),
            arithmetic=(
                "tokens $0.003000 + $0.002700 = $0.005700; Gemini 3.x bills each search request: 3 x $14/1,000 "
                "= $0.042000 (priced past the 5,000/month free allowance); total $0.047700."
            ),
            sources=(GEMINI_PAGE, VERTEX_PAGE),
        ),
        Case(
            id="G3_grounding_via_agent_tool",
            title="Google Search grounding through ADK's GoogleSearchAgentTool (one query, Gemini 3.x)",
            step=Step(g3, prompt=1_000, output=20, calls_tool="google_search_agent"),
            sub_step=Step(g3, prompt=2_000, output=300, grounding_queries=1),
            followup_step=Step(g3, prompt=2_500, output=50),
            kind="cost",
            origin="counter",
            google_search_agent_tool=True,
            # root call 1: 1,000 x $1.50/M + 20 x $9.00/M = $0.001500 + $0.000180 = $0.001680
            # sub-agent (grounded): 2,000 x $1.50/M + 300 x $9.00/M = $0.003000 + $0.002700 = $0.005700
            # root call 2 (final): 2,500 x $1.50/M + 50 x $9.00/M = $0.003750 + $0.000450 = $0.004200
            # tokens $0.011580 ; grounding: 1 query x $14/1,000 = $0.014000 ; total $0.025580
            expected_usd=(
                _usd(g3, 1_000, 0, 20) + _usd(g3, 2_000, 0, 300) + _usd(g3, 2_500, 0, 50) + 0.014
            ),
            incomplete_usd=(
                _usd(g3, 1_000, 0, 20) + _usd(g3, 2_000, 0, 300) + _usd(g3, 2_500, 0, 50),
            ),
            arithmetic=(
                "root call $0.001680 + sub-agent call $0.005700 + root final call $0.004200 = $0.011580 in "
                "tokens; one grounding query = $0.014000; total $0.025580. This is the path on which a "
                "tool-callback fee hook (name-matched on 'google_search') can fire."
            ),
            sources=(GEMINI_PAGE, VERTEX_PAGE),
        ),
        Case(
            id="T1_tool_use_prompt_tokens",
            title="Tokens fetched by a built-in tool (URL context) are billed as input",
            step=Step(f, prompt=1_000, output=200, tool_use_prompt=5_000),
            kind="cost",
            origin="counter",
            # (1,000 + 5,000) x $0.30/M = $0.001800 ; 200 x $2.50/M = $0.000500 ; total $0.002300
            # tool-use tokens left out: 1,000 x $0.30/M + $0.000500 = $0.000800
            expected_usd=_usd(f, 6_000, 0, 200),
            incomplete_usd=(_usd(f, 1_000, 0, 200),),
            arithmetic=(
                "tool_use_prompt_token_count is reported separately from prompt_token_count and is 'counted as "
                "part of the input tokens' (ai.google.dev/gemini-api/docs/url-context): 6,000 x $0.30/M = "
                "$0.001800 + 200 x $2.50/M = $0.000500 = $0.002300."
            ),
            sources=(GEMINI_PAGE, "ai.google.dev/gemini-api/docs/url-context (read 2026-09-21)"),
        ),
        Case(
            id="A1_audio_input",
            title="Audio input tokens have their own, higher rate",
            step=Step(f, prompt=1_200, output=100, audio_prompt=1_000),
            kind="cost",
            origin="counter",
            # text 200 x $0.30/M = $0.000060 ; audio 1,000 x $1.00/M = $0.001000 ; out 100 x $2.50/M = $0.000250
            # total $0.001310 ; audio left out: $0.000060 + $0.000250 = $0.000310
            expected_usd=_usd(f, 200, 0, 100, audio=1_000),
            incomplete_usd=(_usd(f, 200, 0, 100),),
            arithmetic=(
                "prompt_tokens_details splits 1,200 into TEXT 200 and AUDIO 1,000: 200 x $0.30/M = $0.000060; "
                "1,000 x $1.00/M (audio input) = $0.001000; 100 x $2.50/M = $0.000250; total $0.001310. "
                "Pricing all 1,200 at the text rate gives $0.000610, a wrong figure."
            ),
            sources=(GEMINI_PAGE,),
        ),
        Case(
            id="M1_gpt_4o",
            title="A published price for a model outside one tool's table (gpt-4o)",
            step=Step("gpt-4o", prompt=1_000_000, output=100_000),
            kind="cost",
            origin="counter",
            # 1,000,000 x $2.50/M = $2.50 ; 100,000 x $10.00/M = $1.00 ; total $3.50
            expected_usd=_usd("gpt-4o", 1_000_000, 0, 100_000),
            arithmetic="1M x $2.50/M + 100k x $10.00/M = $2.50 + $1.00 = $3.50",
            sources=(
                "developers.openai.com/api/docs/pricing.md, row gpt-4o: $2.50 / $10.00 (read 2026-09-21)",
            ),
        ),
        Case(
            id="M2_claude_opus_5",
            title="A published price for a model outside another tool's table (claude-opus-5)",
            step=Step("claude-opus-5", prompt=1_000_000, output=100_000),
            kind="cost",
            origin="counter",
            # 1,000,000 x $5/M = $5.00 ; 100,000 x $25/M = $2.50 ; total $7.50
            expected_usd=_usd("claude-opus-5", 1_000_000, 0, 100_000),
            arithmetic="1M x $5/M + 100k x $25/M = $5.00 + $2.50 = $7.50",
            sources=(
                "platform.claude.com/docs/en/about-claude/pricing.md, row Claude Opus 5: $5 / $25 (read 2026-09-21)",
            ),
        ),
    ]
