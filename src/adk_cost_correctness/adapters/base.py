"""The adapter contract: everything a cost plugin needs to be scored, and nothing tool-specific."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from ..cases import Case
from ..scoring import Outcome


@dataclass
class RunContext:
    """What the harness hands the adapter after the run, for tools that keep results in session state."""

    session_state: dict[str, Any] = field(default_factory=dict)
    stdout: str = ""


class CostPluginAdapter(Protocol):
    """Implement this once per tool. The harness builds the app, runs the fixture, and scores
    ``collect()``; the adapter never sees the expected cost."""

    name: str

    def version(self) -> str:
        """Package version (and anything else needed to reproduce the run)."""
        ...

    def start(self, case: Case) -> None:
        """Fresh tool state for one case (reset any global/class-level state the tool keeps)."""
        ...

    def plugins(self) -> list[Any]:
        """ADK plugin instances to put in ``App(plugins=...)`` (one, even for the double-registration
        case; the harness adds the second registration through ``agent_kwargs``)."""
        ...

    def agent_kwargs(self) -> dict[str, Any]:
        """Extra kwargs for the ``LlmAgent`` that register the SAME tool a second time, used only for
        the double-registration case, e.g. ``{"after_model_callback": plugin.after_model_callback}``."""
        ...

    def collect(self, ctx: RunContext) -> Outcome:
        """After the run: what the tool reports as the total cost of the run."""
        ...
