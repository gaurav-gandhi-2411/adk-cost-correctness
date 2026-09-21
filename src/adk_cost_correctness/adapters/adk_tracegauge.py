"""Adapter for adk-tracegauge (pip install adk-tracegauge). The scorecard reads the same snapshot
that ``adk-tracegauge report`` prints: priced invocations, and unpriced ones listed as unknown."""

from __future__ import annotations

import importlib.metadata
from typing import Any

from ..cases import Case
from ..scoring import Outcome
from .base import RunContext


class AdkTracegaugeAdapter:
    name = "adk-tracegauge"

    def version(self) -> str:
        return f"adk-tracegauge {importlib.metadata.version('adk-tracegauge')}"

    def start(self, case: Case) -> None:
        from adk_tracegauge import TraceGaugeUsagePlugin
        from adk_tracegauge._store import UsageStore

        self._store = UsageStore()
        self._plugin = TraceGaugeUsagePlugin(store=self._store)

    def plugins(self) -> list[Any]:
        return [self._plugin]

    def agent_kwargs(self) -> dict[str, Any]:
        # The double registration its README warns about: plugins=[...] AND the direct callback.
        return {"after_model_callback": self._plugin.after_model_callback}

    def collect(self, ctx: RunContext) -> Outcome:
        from adk_tracegauge.snapshot import build_snapshot

        snap = build_snapshot(self._store)
        if snap.skipped and not snap.records:
            return Outcome(total_usd=None, flagged=True)
        return Outcome(total_usd=sum(r.cost_usd for r in snap.records), flagged=bool(snap.skipped))
