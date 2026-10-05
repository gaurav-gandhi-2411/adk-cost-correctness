# Scorecards

One file per tool per run. Each is the verbatim output of `adk-cost-correctness run --adapter <name>` and
names the tool version.

| File | Tool | Version | Rule | Result |
|---|---|---|---|---|
| `2026-09-21_adk-tracegauge.md` | adk-tracegauge | 0.8.1 | three outcomes, 12 cases | 6 PASS / 5 INCOMPLETE / 1 FAIL |
| `2026-09-21_adk-tracegauge_0.9.0-flagged.md` | adk-tracegauge | 0.9.0 patched build (`main` `9da795c`, unreleased) | three outcomes, 12 cases | 6 PASS / 6 INCOMPLETE (all flagged) / 0 FAIL |
| `2026-09-21_adk-tracegauge_0.9.0-published-wheel.md` | adk-tracegauge | 0.9.0 PUBLISHED wheel from PyPI (tag `v0.9.0`, `9da795c`) | three outcomes, 12 cases | 6 PASS / 6 INCOMPLETE (all flagged) / 0 FAIL |
| `2026-09-21_adk-tracegauge_0.9.0-published_15cases.md` | adk-tracegauge | 0.9.0 PUBLISHED wheel | three outcomes, 15 cases (G1r-G3r added) | 6 PASS / 8 INCOMPLETE / 1 FAIL (G3r) |
| `2026-09-21_adk-finops_0.6.1_15cases.md` | adk-finops | 0.6.1 PUBLISHED | three outcomes, 15 cases | 4 PASS / 5 INCOMPLETE / 6 FAIL |
| `2026-09-21_adk-tracegauge_dev-pr91_15cases.md` | adk-tracegauge | dev build of PR #91, NOT published | three outcomes, 15 cases | 6 PASS / 9 INCOMPLETE (flagged) / 0 FAIL |
| `2026-09-21_adk-tracegauge_0.9.0-published_15cases_scorerfix.md` | adk-tracegauge | 0.9.0 PUBLISHED wheel, after the scorer fix | three outcomes, 15 cases | 6 PASS / 9 INCOMPLETE / 0 FAIL |
| `2026-09-21_adk-finops_0.6.1_15cases_scorerfix.md` | adk-finops | 0.6.1 PUBLISHED, after the scorer fix | three outcomes, 15 cases | 4 PASS / 5 INCOMPLETE / 6 FAIL (unchanged by the fix) |
| `2026-09-21_adk-tracegauge_0.9.1-published_15cases.md` | adk-tracegauge | 0.9.1 PUBLISHED wheel (`v0.9.1` = `28d4d05`) | three outcomes, 15 cases | 6 PASS / 9 INCOMPLETE (flagged) / 0 FAIL |
| `2026-09-21_adk-finops.md` | adk-finops | 0.6.1 (commit `69ed257`) | three outcomes, 12 cases | 4 PASS / 3 INCOMPLETE / 5 FAIL |
| `2026-09-21_adk-tracegauge_five-cases-pass-fail-rule.md` | adk-tracegauge | 0.8.1 | superseded: pass/fail, original five cases | 5/5 |
| `2026-09-21_adk-finops_five-cases-pass-fail-rule.md` | adk-finops | 0.6.1 | superseded: pass/fail, original five cases | 2/5 |
| `2026-09-23_adk-finops_0.6.3_15cases.md` | adk-finops | 0.6.3 PUBLISHED (retest after issue replies) | three outcomes, 15 cases | 5 PASS / 5 INCOMPLETE / 5 FAIL |
| `2026-10-05_adk-finops_1.0.3_15cases.md` | adk-finops | 1.0.3 PUBLISHED (latest release) | three outcomes, 15 cases | 5 PASS / 5 INCOMPLETE / 5 FAIL (identical to 0.6.3) |

The two superseded files are kept for history: they used the first rule and only the five cases chosen after
the fact (see the README disclosure).

## Reported to the maintainers

Before these scorecards are published, the adk-finops failures found by the ORIGINAL five cases were
reported to its maintainers on **2026-09-21**, one issue per defect, each with a minimal repro, the arithmetic,
and the version tested:

- C1 unknown model priced at the fallback rate: https://github.com/dmoonat/adk-finops/issues/1
- C4 double registration counted twice with no warning: https://github.com/dmoonat/adk-finops/issues/2
- C5 streaming partials each recorded: https://github.com/dmoonat/adk-finops/issues/3

**Status as of 2026-09-23, after retesting 0.6.3 (see `2026-09-23_adk-finops_0.6.3_15cases.md`):**

- **Issue #3 (streaming) — FIXED**, commit `38cbad874a420f4a41ba56efd740e1d143aa6e1f`, 2026-09-21.
  Verified: the real-stream fixture now reports $0.0005239, matching expected exactly (was $0.0020673,
  3.95x). Maintainer replied 2026-09-21 confirming the fix; retest reply posted
  https://github.com/dmoonat/adk-finops/issues/3#issuecomment-5788530223.
- **Issue #1 (unknown model) — NOT FIXED (partial).** Commit `d43d8b247aa09c7815c80090960f5b95ab614a9c`,
  2026-09-21, adds a one-time logged/printed warning and an internal `is_fallback` flag, but the reported
  total still carries the fallback dollar figure unflagged ($0.5500000 for `claude-opus-5`, still FAIL
  under the suite's rule). Retest reply posted
  https://github.com/dmoonat/adk-finops/issues/1#issuecomment-5788531028.
- **Issue #2 (double registration) — NOT FIXED (docs only).** Commit
  `f0569737a3ebd91dbe4efd219817a312db9f8d78`, 2026-09-21, adds a README warning; no runtime detection or
  refusal. Retest still shows $0.0016000 (2.00x) against expected $0.0008000. Retest reply posted
  https://github.com/dmoonat/adk-finops/issues/2#issuecomment-5788531285.

A scorecard is a statement about one version on one date; the 2026-09-21 (0.6.1) scorecards are kept as
scored, and `2026-09-23_adk-finops_0.6.3_15cases.md` supersedes them for the current release.

**adk-finops G3r (2026-09-21), recorded here and NOT filed as an issue** (its first three issues were answered by the maintainer on 2026-09-21 and 2026-09-23; see the quotes in the 2026-10-05 scorecard and the README disclosure): through `GoogleSearchAgentTool` on a Gemini 2.5 call it reported $0.0161853 = tokens $0.0021853 + $0.014, the Gemini 3.x per-query grounding rate applied to a 2.5 call; the published 2.5 fee is $35 per 1,000 grounded prompts ($0.035), so the figure is 0.44x of the expected $0.0371853.

Scorer note: the two `..._15cases.md` files for the published tools were scored before a scorer bug fix (SCORING.md, scorer changelog); they are kept as scored, and the `..._scorerfix.md` files supersede them. Only adk-tracegauge 0.9.0 on G3r changed (FAIL to INCOMPLETE).

The counter-cases produced further results that have NOT been separately reported: adk-finops FAIL on M2
(claude-opus-5 priced at the fallback rate, the same mechanism as issue 1) and on A1 (audio at the text rate,
which adk-tracegauge also fails), and INCOMPLETE results for both tools on grounding fees and tool-use
tokens. adk-tracegauge's own gaps are listed in its scorecard.
