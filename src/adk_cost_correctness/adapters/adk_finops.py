"""Adapter for adk-finops (pip install adk-finops). Reads the summary the plugin itself stores in
session state after the run (``finops_cost``) -- the figure a user of the plugin is shown."""

from __future__ import annotations

import importlib.metadata
from typing import Any

from ..cases import Case
from ..scoring import Outcome
from .base import RunContext


class AdkFinopsAdapter:
    name = "adk-finops"

    def version(self) -> str:
        return f"adk-finops {importlib.metadata.version('adk-finops')}"

    def start(self, case: Case) -> None:
        from adk_finops import CostTracker, FinOpsCostPlugin

        CostTracker.reset()  # the tracker keeps class-level state across runs
        self._plugin = FinOpsCostPlugin(
            render_terminal_box=False, enable_optimization_advisor=False
        )

    def plugins(self) -> list[Any]:
        return [self._plugin]

    def agent_kwargs(self) -> dict[str, Any]:
        return {"after_model_callback": self._plugin.after_model_callback}

    def collect(self, ctx: RunContext) -> Outcome:
        summary = ctx.session_state.get("finops_cost")
        if not summary:
            return Outcome(total_usd=None)
        session = summary.get("session") or summary
        total = session.get("total_cost_usd")
        return Outcome(total_usd=None if total is None else float(total))
