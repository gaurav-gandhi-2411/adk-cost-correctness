"""``adk-cost-correctness run --adapter adk-tracegauge`` prints the scorecard for one tool."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import json
import platform
import sys
from collections import Counter

from .cases import all_cases
from .harness import run_all

# Read from the installed distributions at run time, so a scorecard names what actually ran rather than
# what a command line asked for (pip and uv can both resolve something other than the requested range).
RESOLVED_DISTRIBUTIONS = ("google-adk", "google-genai")


def resolved_versions() -> dict[str, str]:
    """The google-adk, google-genai and Python versions installed in this environment."""
    versions = {d: importlib.metadata.version(d) for d in RESOLVED_DISTRIBUTIONS}
    versions["python"] = platform.python_version()
    return versions


ADAPTERS = {
    "adk-tracegauge": ("adk_cost_correctness.adapters.adk_tracegauge", "AdkTracegaugeAdapter"),
    "adk-finops": ("adk_cost_correctness.adapters.adk_finops", "AdkFinopsAdapter"),
    "reference": ("adk_cost_correctness.adapters.reference", "ReferenceAdapter"),
    "naive": ("adk_cost_correctness.adapters.reference", "NaiveAdapter"),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="adk-cost-correctness", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run", help="score one adapter on every case")
    run.add_argument("--adapter", required=True, choices=sorted(ADAPTERS))
    run.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    module, cls = ADAPTERS[args.adapter]
    adapter = getattr(importlib.import_module(module), cls)()
    cases = {c.id: c for c in all_cases()}
    scores = run_all(adapter)
    sanity = next(s for s in scores if s.case_id == "S0_sanity")
    graded = [s for s in scores if s.case_id != "S0_sanity"]
    tally = Counter(s.verdict for s in graded)
    resolved = resolved_versions()

    if args.json:
        payload = {
            "tool": adapter.version(),
            "resolved": resolved,
            "sanity_passed": sanity.passed,
            "tally": {v: tally.get(v, 0) for v in ("PASS", "INCOMPLETE", "FAIL")},
            "of": len(graded),
            "cases": [{**s.__dict__, "origin": cases[s.case_id].origin} for s in scores],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(f"Scorecard: {adapter.version()}")
        print("Resolved: " + ", ".join(f"{name} {v}" for name, v in resolved.items()))
        print(f"{'case':30} {'origin':9} {'result':11} detail")
        for s in scores:
            print(f"{s.case_id:30} {cases[s.case_id].origin:9} {s.verdict:11} {s.reason}")
        print(
            f"\nPASS {tally.get('PASS', 0)} / INCOMPLETE {tally.get('INCOMPLETE', 0)} / "
            f"FAIL {tally.get('FAIL', 0)} of {len(graded)} graded cases"
            f" (sanity {'ok' if sanity.passed else 'FAILED: scorecard invalid'})"
        )
    return 0 if sanity.passed else 2


if __name__ == "__main__":
    sys.exit(main())
