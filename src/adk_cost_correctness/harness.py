"""Builds the same ADK app for every tool, runs one fixture through a real ``InMemoryRunner``, and
scores what the adapter reports. The model is a deterministic replay; no network, no API key."""

from __future__ import annotations

import asyncio
import contextlib
import io
from typing import Any

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.run_config import (  # type: ignore[attr-defined]  # ADK re-exports it without __all__
    RunConfig,
    StreamingMode,
)
from google.adk.apps.app import App
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import InMemoryRunner
from google.genai import types as T

from .adapters.base import CostPluginAdapter, RunContext
from .cases import Case, Step, all_cases
from .scoring import Score, score


def _usage(step: Step, output: int, *, final: bool) -> Any:
    return T.GenerateContentResponseUsageMetadata(
        prompt_token_count=step.prompt,
        candidates_token_count=output,
        cached_content_token_count=step.cached or None,
        thoughts_token_count=(step.thoughts or None) if final else None,
        total_token_count=step.prompt + output + (step.thoughts if final else 0),
    )


def _replay_model(step: Step) -> BaseLlm:
    class Replay(BaseLlm):
        model: str = "replay-fake"

        @classmethod
        def supported_models(cls) -> list[str]:
            return ["replay-fake"]

        async def generate_content_async(self, llm_request: Any, stream: bool = False) -> Any:
            content = T.Content(role="model", parts=[T.Part(text="ok")])
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
                usage_metadata=_usage(step, step.output, final=True),
            )

    return Replay()


async def _run(case: Case, adapter: CostPluginAdapter) -> tuple[str | None, RunContext]:
    extra = adapter.agent_kwargs() if case.register_twice else {}
    agent = LlmAgent(
        name="root_agent", model=_replay_model(case.step), instruction="Reply.", **extra
    )
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
