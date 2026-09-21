"""Adapter for adk-finops (pip install adk-finops).

The total is the sum of every SESSION the tracker recorded. adk-finops runs an ``AgentTool`` sub-agent as
its own session, so the root session's summary (the ``finops_cost`` value the plugin stores in session
state) leaves the sub-agent out; the cases that use a sub-agent (G3) would then be scored on a figure
no user is shown in one place. Summing the sessions is the total cost of the run. The tracker keys each
run twice (by turn id, ``e-...``, and by session id); only the session-level entries are summed. This reads
a private attribute (``CostTracker._active_runs``) because the package has no public accessor for it.
"""

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
        from adk_finops import CostTracker

        sessions = {
            key: run
            for key, run in CostTracker._active_runs.items()
            if not str(key).startswith("e-")
        }
        if not sessions:
            summary = ctx.session_state.get("finops_cost")
            if not summary:
                return Outcome(total_usd=None)
            total = (summary.get("session") or summary).get("total_cost_usd")
            return Outcome(total_usd=None if total is None else float(total))
        return Outcome(
            total_usd=sum(float(r.get("total_cost_usd") or 0.0) for r in sessions.values())
        )
