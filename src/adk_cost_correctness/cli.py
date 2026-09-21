"""``adk-cost-correctness run --adapter adk-tracegauge`` prints the scorecard for one tool."""

from __future__ import annotations

import argparse
import importlib
import json
import sys

from .cases import all_cases
from .harness import run_all

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
    passed = sum(s.passed for s in graded)

    if args.json:
        print(
            json.dumps(
                {
                    "tool": adapter.version(),
                    "sanity_passed": sanity.passed,
                    "passed": passed,
                    "of": len(graded),
                    "cases": [s.__dict__ for s in scores],
                },
                indent=2,
            )
        )
    else:
        print(f"Scorecard: {adapter.version()}")
        print(f"{'case':26} {'result':6} detail")
        for s in scores:
            print(f"{s.case_id:26} {'PASS' if s.passed else 'FAIL':6} {s.reason}")
        print(
            f"\n{passed}/{len(graded)} graded cases passed"
            f" (sanity {'ok' if sanity.passed else 'FAILED: scorecard invalid'});"
            f" streaming fixture verified on a real stream: {cases['C5_streaming_partials'].verified_on_real_stream}"
        )
    return 0 if sanity.passed else 2


if __name__ == "__main__":
    sys.exit(main())
