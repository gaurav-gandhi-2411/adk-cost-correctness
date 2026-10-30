# Measuring cost correctness in ADK agent cost tools

*This page, in the [adk-cost-correctness](https://github.com/gaurav-gandhi-2411/adk-cost-correctness) repository, is
the canonical copy; any cross-post points here. Every number below is from a scorecard committed in that repository
(path in brackets, under `scorecards/`). The author maintains one of the two tools scored; see "Disclosure".*

A cost tool for an agent framework prints dollar figures. Whether the figure is right is a separate question
that its test suite usually answers with the tool's own fixtures. This post describes a small suite that asks
the question from outside, what it found for two ADK cost tools, and what it cannot tell you.

## The suite

`adk-cost-correctness` has 15 graded cases. Each runs one deterministic fixture through ADK's real
`InMemoryRunner`, with a replayed model: no network, no key. The expected dollar figure is computed by hand
from published vendor rates, with the arithmetic written in the case.

The cases cover: a model with no published price (C1), cached tokens (C2), thinking tokens (C3), a plugin
registered twice (C4), streamed chunks that carry cumulative usage (C5), Google Search grounding fees on
Gemini 2.5, Gemini 3.x and through `GoogleSearchAgentTool` (G1, G2, G3), the same three rebuilt with the token
counts of real grounded responses (G1r, G2r, G3r), tokens fetched by a built-in tool (T1), audio input (A1),
and published prices for models outside one tool's table (M1: gpt-4o, M2: claude-opus-5).

## Three outcomes, not two

A pass/fail rule rewards a tool that answers "unknown" to everything. So each case ends in one of three
states:

- **PASS**: the reported figure matches the expected one.
- **INCOMPLETE**: the tool did not give a figure, or said its figure leaves something out, where a price is
  published. It did not guess.
- **FAIL**: a wrong figure, or any guess for something that cannot be priced.

A tool that declares "this total excludes the grounding fee" scores INCOMPLETE, not PASS. It is not wrong, and
it is not done. The rule is in `docs/SCORING.md`, together with a changelog of scorer fixes; one of them
(a declared lower bound scored FAIL) was found by scoring the author's own tool.

## One fixture is a recording

C5 replays a real Gemini stream. A number in it looked wrong (19 against 38 prompt tokens) and was traced to
its cause against the API itself; the provenance is in `docs/FIXTURE_PROVENANCE.md`.

## Results

| Tool and version | PASS | INCOMPLETE | FAIL | Scorecard |
|---|---|---|---|---|
| adk-tracegauge 0.9.1 (PyPI) | 6 | 9 | 0 | `2026-09-21_adk-tracegauge_0.9.1-published_15cases.md` |
| adk-tracegauge 0.10.0 (PyPI) | 11 | 4 | 0 | `2026-10-07_adk-tracegauge_0.10.0-published_15cases.md` |
| adk-tracegauge 0.10.1 (PyPI, latest) | 11 | 4 | 0 | `2026-10-09_adk-tracegauge_0.10.1-published_15cases.md` |
| adk-finops 1.0.3 (PyPI) | 5 | 5 | 5 | `2026-10-05_adk-finops_1.0.3_15cases.md` |

All scored on google-adk 2.9.2. The re-scores on newer releases are identical, every case to the cent, verdicts
and detail text included: adk-tracegauge 0.10.1 on google-adk 2.11.0, 2.12.0 and 2.13.0, and adk-finops 1.0.3 on
2.12.0 and 2.13.0 (`2026-10-19_adk-tracegauge_0.10.1_adk-2.12.0_15cases.md`,
`2026-10-19_adk-finops_1.0.3_adk-2.12.0_15cases.md`, `2026-10-26_adk-tracegauge_0.10.1_adk-2.13.0_15cases.md`,
`2026-10-26_adk-finops_1.0.3_adk-2.13.0_15cases.md`).
The other rows were not re-scored on newer releases. The 0.10.1 release adds
`--version`, type information and a vendor-shutdown rule that took effect on 2026-10-23. The 2.13.0 re-score ran
on 2026-10-26, after that date, and is unchanged, because no case uses one of the four models shut down that day.
The 0.10.0 row was scored on the published wheel; the same code scored identically (every case, to the cent) on the unreleased `main` build
(`2026-10-07_adk-tracegauge_main-921ac68_0.10.0-candidate_15cases.md`) before release, against an outcome
written down in advance.

**adk-finops** fails C1, C4, G3r, A1 and M2. The maintainer called C1 and C4 intended behaviour; M2 shares C1's mechanism and was not reported separately. On C1
(a model with no published price priced at a fallback rate) the maintainer wrote on 2026-09-23: "We are not
doing a pre-check whether model pricing is available or not, and output will reflect the tokens so user can
calculate with the available price or better way is to register it with the package as mentioned here." On C4 (a doubly
registered plugin counts every call twice), on 2026-09-21: "This behavior is expected as adk-finops is a adk
plugin." The suite's rule is that a cost tool must not report a figure for an unpriced model and must not
silently double-count; the maintainer disagrees. Read C1, C4 and M2 as "this suite's rule says FAIL", not as
"a bug". A streaming defect (C5) was acknowledged and fixed upstream.

**adk-tracegauge 0.9.1** never FAILs here and is INCOMPLETE on nine cases, because it declares what it leaves
out: grounding fees, tool-use tokens, audio input and a model missing from its table.

## What adk-tracegauge still gets INCOMPLETE on

In 0.10.1 (identical to 0.10.0 here), four cases remain INCOMPLETE:

- **G2, G3, G2r**: Gemini 3.x grounding. It is billed per search query, and no real capture exists (grounded 3.x requests on a free-tier key returned 429; the cause is not established), so the expected figure comes from the published rate alone.
- **T1**: tokens fetched by a built-in tool (URL context). Their billing treatment differs by tool and is not
  documented for this one.

Five INCOMPLETE cases (G1, G1r, G3r, A1, M1) became PASS by pricing things the vendor publishes a price for: audio input where a
page lists an audio rate, per-model cached rates (gpt-4o caches at 0.5x of input, gpt-4.1 at 0.25x, not the
0.1x the table assumed), and the Google Search grounding fee on the Gemini API for Gemini 2.5. A total that
includes a grounding fee is labelled an upper bound, because Google's free allowance cannot be seen from a
plugin.

One of those changes touched the suite itself: its replay model exposed no backend, so a tool that refuses to
price a grounding fee unless it can read that the Gemini API served the call could not be scored on grounding
at all. The harness now replays `gemini-*` models through ADK's own `Gemini` class. With the harness
unchanged the same build scores 8 PASS, 7 INCOMPLETE, 0 FAIL; both numbers are in the repository, and the
change moved no earlier result.

## A lesson from a different benchmark

`eval-defect-bench` tried to detect defects in code that evaluates agents. Its ground truth was "the bug the
paired historical commit fixed". A frontier judge that flagged a real, different defect in the same function
counted as wrong. The judge flagged 4 of 30 buggy functions. Scored against the paired commit, 2 matched; scored by "is there a
genuine defect here", all 4 were real, 2 of them a different defect from the paired one. The two questions are *did the judge explain this
commit* and *did it discriminate a buggy function from a clean one*, and only the second was the capability
under test. Discrimination itself was weak: balanced accuracy 53.3% (adjudicated) for the frontier judge and
58.3% for a local-model consensus, d-prime 0.39 and 0.42.

Cost tools have the same trap. A case that checks whether a tool narrates "grounding was not priced" is not a
case that checks the figure. Each case here scores the dollar figure and the completeness flag separately.

## Disclosure

The author maintains adk-tracegauge. The five original cases were chosen after a hands-on comparison showed
where adk-finops fell short on them; the counter-cases were added the same day, committed before either tool
was scored on them, and no case or rule changed after scoring. Which counter-cases to write was still the
author's choice. The suite says nothing about budget guards, exporters or dashboards. To contest a fixture or
an adapter, open an issue with the arithmetic.
