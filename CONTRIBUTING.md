# Contributing

Two kinds of contribution: a new case, or an adapter for another cost tool. Both must keep the suite's
core promise: every expected figure is hand-computed and visible, and the suite can be satisfied.

## Add a case

1. Add a `Case` to `all_cases()` in `src/adk_cost_correctness/cases.py`.
   - **Write the arithmetic in a comment and in `arithmetic=`, from the published rate set at the top of
     that file.** Do not compute the expected value by running a tool. If a number comes from a real API
     response, record the response in `src/adk_cost_correctness/data/` with provenance (model, date, how it
     was captured), as C5 does.
   - `kind="cost"`: one correct dollar figure; add `incomplete_usd=` for each figure that means "priced, but a
     published component was left out" (INCOMPLETE, not FAIL). `kind="unpriced"`: there is no correct figure
     and any reported figure fails (see `docs/SCORING.md`). `kind="cost_or_refusal"`: a tool may also refuse.
   - Mark `origin="counter"` for a case added to balance an earlier selection, and record `added_on`. Commit
     new cases and rule changes BEFORE scoring any tool on them, and do not change them after.
   - Check the case against the in-repo naive plugin: a case that everything passes measures nothing. Do not
     score the tools you are grading on it before committing it.
2. Make the in-repo plugins behave accordingly: `ReferencePlugin` must pass it, `NaivePlugin` must fail it
   for the reason the case exists (`adapters/reference.py`). Add the assertion to
   `tests/test_suite.py` (`test_the_naive_plugin_does_not_pass_the_cases_it_is_wrong_on`).
3. If it needs a new scoring behaviour, change `scoring.py` and add unit tests with synthetic outcomes for
   both the pass and the fail side.
4. Update the case table in `README.md` and the relevant section of `docs/SCORING.md`. Re-run every
   adapter's scorecard and save the output under `scorecards/` (see below).

## Add an adapter for another tool

Implement `CostPluginAdapter` (`src/adk_cost_correctness/adapters/base.py`):

- `version()`: the exact package version (and commit, if you know it).
- `start(case)`: fresh tool state; reset anything the tool keeps at class or module level.
- `plugins()`: the plugin instance(s) for `App(plugins=...)`.
- `agent_kwargs()`: the extra `LlmAgent` kwargs that register the SAME tool a second time (only used for the
  double-registration case), e.g. `{"after_model_callback": plugin.after_model_callback}`.
- `collect(ctx)`: after the run, what the tool reports as the total: an `Outcome(total_usd=..., flagged=...)`.
  Read it the way a user of the tool sees it (its summary, report, or exported figure), not from internals
  that a user never looks at. Return `total_usd=None` if the tool reports no figure for the run.

The adapter never sees the expected cost. Then:

1. Add it to `ADAPTERS` in `cli.py` and an optional extra in `pyproject.toml`.
2. Run `adk-cost-correctness run --adapter <name>` and save the verbatim output to
   `scorecards/<date>_<name>.md` with the tool version.
3. Check the sanity case (S0) passes: if not, the adapter is misreading the tool and the scorecard is
   invalid.
4. If a case fails, reduce it to a minimal repro and, if it is a defect, report it to the tool's maintainers
   with the arithmetic before publishing the scorecard.

## Standards

Python 3.10+, `from __future__ import annotations`, `ruff check` + `ruff format`, `mypy --strict` on `src/`
(configured in `pyproject.toml`, but not clean today: with google-adk 2.12.0, mypy 1.14.1 reports 2 errors,
`harness.py:77` and `cli.py:42`, and mypy 2.4.0 reports the first; fixes are welcome, and the code runs and
tests pass regardless),
tests named `test_*.py`. Disclose any affiliation with a tool you score (see the README).
