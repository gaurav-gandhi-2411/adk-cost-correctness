"""Builds the same ADK app for every tool, runs one fixture through a real ``InMemoryRunner``, and
scores what the adapter reports. The model is a deterministic replay; no network, no API key."""

from __future__ import annotations

import asyncio
import contextlib
import io
import os
from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.run_config import (  # type: ignore[attr-defined]  # ADK re-exports it without __all__
    RunConfig,
    StreamingMode,
)
from google.adk.apps.app import App
from google.adk.models.base_llm import BaseLlm
from google.adk.models.google_llm import Gemini
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.adk.tools.google_search_agent_tool import (
    GoogleSearchAgentTool,
    create_google_search_agent,
)
from google.adk.tools.google_search_tool import google_search
from google.genai import types as T

from .adapters.base import CostPluginAdapter, RunContext
from .cases import Case, Step, all_cases
from .scoring import Score, score


def _usage(step: Step, output: int, *, final: bool) -> Any:
    details = None
    if step.audio_prompt:
        details = [
            T.ModalityTokenCount(
                modality=T.MediaModality.TEXT, token_count=step.prompt - step.audio_prompt
            ),
            T.ModalityTokenCount(modality=T.MediaModality.AUDIO, token_count=step.audio_prompt),
        ]
    tool_use = step.tool_use_prompt or None
    return T.GenerateContentResponseUsageMetadata(
        prompt_token_count=step.prompt,
        candidates_token_count=output,
        cached_content_token_count=step.cached or None,
        thoughts_token_count=(step.thoughts or None) if final else None,
        tool_use_prompt_token_count=tool_use if final else None,
        prompt_tokens_details=details,
        total_token_count=(
            step.prompt + output + ((step.thoughts + step.tool_use_prompt) if final else 0)
        ),
    )


def _content(step: Step) -> Any:
    if step.calls_tool:
        part = T.Part(
            function_call=T.FunctionCall(id="c1", name=step.calls_tool, args={"request": "q"})
        )
    else:
        part = T.Part(text="ok")
    return T.Content(role="model", parts=[part])


def _replay_model(steps: list[Step], *, name: str = "replay-fake") -> BaseLlm:
    """Serves ``steps`` in order, one per model call.

    A model named ``gemini-*`` is a subclass of ADK's own ``Gemini`` class, so the app a tool sees
    reports its backend exactly as a real Gemini API app does (``api_client.vertexai`` is False, read
    from a client built offline from a placeholder key). Before this change (suite commit
    ``eac41ec`` and earlier) every replay model was a bare ``BaseLlm`` with no ``api_client`` at all,
    which no real Gemini deployment looks like; a tool that refuses to price a grounding fee unless
    it can positively identify the Gemini API backend could therefore never be scored on it. The
    same harness serves every adapter."""
    # BaseLlm is abstract, but it is only ever subclassed below (Replay implements the abstract
    # method), never instantiated, so mypy's type-abstract check does not apply.
    base: type[BaseLlm] = BaseLlm  # type: ignore[type-abstract]
    if name.startswith("gemini"):
        base = Gemini
        os.environ.setdefault("GOOGLE_API_KEY", "offline-replay-placeholder-key")

    class Replay(base):  # type: ignore[valid-type, misc]
        model: str = name
        _n: int = 0

        @classmethod
        def supported_models(cls) -> list[str]:
            return [name]

        async def generate_content_async(self, llm_request: Any, stream: bool = False) -> Any:
            step = steps[min(self._n, len(steps) - 1)]
            self._n += 1
            content = _content(step)
            grounding = (
                T.GroundingMetadata(
                    web_search_queries=[f"q{i}" for i in range(step.grounding_queries)]
                )
                if step.grounding_queries
                else None
            )
            for cumulative_out in step.partial_outputs:  # Gemini reports cumulative usage per chunk
                yield LlmResponse(
                    model_version=step.model,
                    content=content,
                    partial=True,
                    usage_metadata=_usage(step, cumulative_out, final=False),
                )
            yield LlmResponse(
                model_version=step.model,
                content=content,
                grounding_metadata=grounding,
                usage_metadata=_usage(step, step.output, final=True),
            )

    return Replay()


def _build_agent(case: Case, extra: dict[str, Any]) -> LlmAgent:
    if case.google_search_agent_tool:
        assert case.sub_step is not None
        sub_model = _replay_model([case.sub_step], name=case.sub_step.model)
        tool = GoogleSearchAgentTool(create_google_search_agent(sub_model))
        assert case.followup_step is not None
        root_steps = [case.step, case.followup_step]
        return LlmAgent(
            name="root_agent",
            model=_replay_model(root_steps, name=case.step.model),
            instruction="Use the search tool.",
            tools=[tool],
        )
    kwargs: dict[str, Any] = dict(extra)
    model_name = "replay-fake"
    if case.builtin_google_search:
        kwargs["tools"] = [google_search]  # ADK's real built-in tool; it checks the model name
        model_name = case.step.model
    return LlmAgent(
        name="root_agent",
        model=_replay_model([case.step], name=model_name),
        instruction="Reply.",
        **kwargs,
    )


async def _run(case: Case, adapter: CostPluginAdapter) -> tuple[str | None, RunContext]:
    extra = adapter.agent_kwargs() if case.register_twice else {}
    agent = _build_agent(case, extra)
    app = App(name="cost_correctness", root_agent=agent, plugins=adapter.plugins())
    runner = InMemoryRunner(app=app)
    session = await runner.session_service.create_session(app_name=app.name, user_id="u")
    config = RunConfig(streaming_mode=StreamingMode.SSE) if case.streaming else RunConfig()
    refused: str | None = None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):  # some tools print on every call
        try:
            async for _ in runner.run_async(
                user_id="u",
                session_id=session.id,
                run_config=config,
                new_message=T.Content(role="user", parts=[T.Part(text="go")]),
            ):
                pass
        except Exception as e:
            refused = f"{type(e).__name__}: {e}"
    final = await runner.session_service.get_session(
        app_name=app.name, user_id="u", session_id=session.id
    )
    state = dict(final.state) if final and final.state else {}
    return refused, RunContext(session_state=state, stdout=buf.getvalue())


def run_case(case: Case, adapter: CostPluginAdapter) -> Score:
    adapter.start(case)
    refused, ctx = asyncio.run(_run(case, adapter))
    outcome = adapter.collect(ctx)
    if refused and outcome.refused is None:
        outcome = type(outcome)(
            total_usd=outcome.total_usd, flagged=outcome.flagged, refused=refused
        )
    return score(case, outcome)


def run_all(adapter: CostPluginAdapter) -> list[Score]:
    return [run_case(c, adapter) for c in all_cases()]
