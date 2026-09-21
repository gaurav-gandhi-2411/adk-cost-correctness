# Scorecards

One file per tool per run. Each is the verbatim output of `adk-cost-correctness run --adapter <name>` and
names the tool version.

| File | Tool | Version | Result |
|---|---|---|---|
| `2026-09-21_adk-tracegauge.md` | adk-tracegauge | 0.8.1 | 5/5 |
| `2026-09-21_adk-finops.md` | adk-finops | 0.6.1 (commit `69ed257`) | 2/5: C1, C4, C5 fail |

## Reported to the maintainers

Before these scorecards are published, each failing case was reported to the adk-finops maintainers on
**2026-09-21**, one issue per defect, each with a minimal repro, the arithmetic, and the version tested:

- C1 unknown model priced at the fallback rate: https://github.com/dmoonat/adk-finops/issues/1
- C4 double registration counted twice with no warning: https://github.com/dmoonat/adk-finops/issues/2
- C5 streaming partials each recorded: https://github.com/dmoonat/adk-finops/issues/3

As of the date the suite was prepared for publication these had not been answered; the maintainers'
response, if any, and any fix should be recorded here before the scorecard is published or re-run against a
newer release. A scorecard is a statement about one version on one date.
