# Scorecards

One file per tool per run. Each is the verbatim output of `adk-cost-correctness run --adapter <name>` and
names the tool version.

| File | Tool | Version | Rule | Result |
|---|---|---|---|---|
| `2026-09-21_adk-tracegauge.md` | adk-tracegauge | 0.8.1 | three outcomes, 12 cases | 6 PASS / 5 INCOMPLETE / 1 FAIL |
| `2026-09-21_adk-tracegauge_0.9.0-flagged.md` | adk-tracegauge | 0.9.0 patched build (`main` `9da795c`, unreleased) | three outcomes, 12 cases | 6 PASS / 6 INCOMPLETE (all flagged) / 0 FAIL |
| `2026-09-21_adk-finops.md` | adk-finops | 0.6.1 (commit `69ed257`) | three outcomes, 12 cases | 4 PASS / 3 INCOMPLETE / 5 FAIL |
| `2026-09-21_adk-tracegauge_five-cases-pass-fail-rule.md` | adk-tracegauge | 0.8.1 | superseded: pass/fail, original five cases | 5/5 |
| `2026-09-21_adk-finops_five-cases-pass-fail-rule.md` | adk-finops | 0.6.1 | superseded: pass/fail, original five cases | 2/5 |

The two superseded files are kept for history: they used the first rule and only the five cases chosen after
the fact (see the README disclosure).

## Reported to the maintainers

Before these scorecards are published, the adk-finops failures found by the ORIGINAL five cases were
reported to its maintainers on **2026-09-21**, one issue per defect, each with a minimal repro, the arithmetic,
and the version tested:

- C1 unknown model priced at the fallback rate: https://github.com/dmoonat/adk-finops/issues/1
- C4 double registration counted twice with no warning: https://github.com/dmoonat/adk-finops/issues/2
- C5 streaming partials each recorded: https://github.com/dmoonat/adk-finops/issues/3

As of the date the suite was prepared for publication these had not been answered; the maintainers'
response, if any, and any fix should be recorded here before the scorecard is published or re-run against a
newer release. A scorecard is a statement about one version on one date.

The counter-cases produced further results that have NOT been separately reported: adk-finops FAIL on M2
(claude-opus-5 priced at the fallback rate, the same mechanism as issue 1) and on A1 (audio at the text rate,
which adk-tracegauge also fails), and INCOMPLETE results for both tools on grounding fees and tool-use
tokens. adk-tracegauge's own gaps are listed in its scorecard.
