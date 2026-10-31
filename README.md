# adk-cost-correctness

A tool-agnostic correctness suite for Google ADK cost-tracking plugins: twelve deterministic cases with
hand-computed expected costs and vendor-sourced prices, scored PASS / INCOMPLETE / FAIL. Any plugin can be
scored by writing one small adapter.

**Write-up:** [Measuring cost correctness in ADK agent cost tools](https://github.com/gaurav-gandhi-2411/adk-cost-correctness/blob/main/docs/measuring-cost-correctness.md) (what the suite found for two tools, and what it cannot tell you).

| Case | What it checks | Added |
|---|---|---|
| C1 unknown model | A model with no published price is reported as unknown, not priced. A guess fails, even a close one. | original five |
| C2 cached tokens | The cached part of the prompt is billed at the cached rate. | original five |
| C3 thinking tokens | Thinking tokens are counted and billed as output. | original five |
| C4 double registration | The same plugin registered twice does not double the cost silently. | original five |
| C5 streaming partials | Cumulative usage on every streamed chunk is priced once. Replayed from a real Gemini stream. | original five |
| G1 / G2 | Google Search grounding fee, Gemini 2.5 (per grounded prompt) and Gemini 3.x (per query), ADK's built-in tool. | counter-case |
| G3 | The same fee through ADK's `GoogleSearchAgentTool` (the path a tool-callback fee hook can fire on). | counter-case |
| G1r / G2r / G3r | G1-G3 rebuilt with the token counts of real Gemini 2.5 grounded responses, which always carry tool-use tokens (G1-G3 do not, so they are not representative of real responses). Tool-use tokens left out or folded in at the input rate both pass. | counter-case, added after real captures |
| T1 | Tokens fetched by a built-in tool (URL context) are billed as input. | counter-case |
| A1 | Audio input tokens have their own, higher rate. | counter-case |
| M1 / M2 | A published price for a model outside a tool's table: gpt-4o, claude-opus-5. | counter-case |

Each case ends **PASS**, **INCOMPLETE** (unknown or omitted where a price is published) or **FAIL** (a wrong
figure, or any guess for an unpriceable component); see `docs/SCORING.md`.

## Run it

```bash
uv sync --frozen --all-extras --python 3.12
uv run --frozen adk-cost-correctness run --adapter adk-tracegauge
uv run --frozen adk-cost-correctness run --adapter adk-finops
```

`uv.lock` pins google-adk, both tools and every transitive dependency, and CI installs from it, so a
scorecard can be reproduced exactly. The scorecard's second line (`Resolved: google-adk ..., google-genai ...,
python ...`) names what was actually installed. The suite needs Python 3.11+ (3.10 is end-of-life, and
google-adk 2.12+ need 3.11+), so the lock resolves a single google-adk version. To score a different version, update the lock
in the same change (`uv lock --upgrade-package adk-tracegauge`, or `--upgrade-package google-adk`).
`pip install -e ".[adk-tracegauge,adk-finops]"` still works, but resolves whatever is newest that day.

No API key and no network: the model is a deterministic replay behind a real `InMemoryRunner`.

## Scorecards (2026-09-21 to 2026-10-05, google-adk 2.9.2)

**15 graded cases** (the 12 below plus the realistic twins G1r-G3r, committed before scoring). The 12-case rows are kept as scored.

| Tool | Version | PASS | INCOMPLETE | FAIL |
|---|---|---|---|---|
| adk-tracegauge | 0.8.1 | 6 | 5 (G1, G2, G3, T1, M1) | 1 (A1 audio) |
| adk-tracegauge | 0.9.0 patched build (`main` `9da795c`, unreleased) | 6 | 6 (G1, G2, G3, T1, A1, M1), all reported as incomplete by the tool | 0 |
| adk-finops | 0.6.1 (commit `69ed257`) | 4 | 3 (G1, G2, T1) | 5 (C1, C4, C5, A1, M2) |
| **15 cases:** adk-tracegauge | **0.9.0 published (PyPI)**, scorer fixed | 6 | 9 (G1, G2, G3, G1r, G2r, G3r, T1, A1, M1) | 0. G3r is INCOMPLETE: 0.9.0 reported the tool-use sub-agent invocation unknown and said the total excludes it (a declared lower bound). It scored FAIL under a scorer bug, fixed after seeing it; see `docs/SCORING.md`'s scorer changelog |
| **15 cases:** adk-tracegauge | **0.9.1 published (PyPI)** | 6 | 9 (G1, G2, G3, G1r, G2r, G3r, T1, A1, M1); every real-shape grounded twin now prices its tokens and reports the tool-use tokens and the grounding fee as flagged | 0 |
| **15 cases:** adk-finops | **0.6.1 published (PyPI)** | 4 | 5 (G1, G2, G1r, G2r, T1) | 6 (C1, C4, C5, G3r, A1, M2): G3r applies the Gemini 3.x $0.014 per-query rate to a Gemini 2.5 call (not reported upstream) |
| **15 cases:** adk-finops | **0.6.3 published (PyPI)**, after issues #1-#3 replies | 5 | 5 (G1, G2, G1r, G2r, T1) | 5 (C1, C4, G3r, A1, M2): C5 moved FAIL→PASS (streaming fix, issue #3, confirmed); C1 and C4 unchanged (issues #1/#2 partial/not fixed — see `scorecards/README.md`) |
| **15 cases:** adk-finops | **1.0.3 published (PyPI)**, latest release, scored 2026-10-05 | 5 | 5 (G1, G2, G1r, G2r, T1) | 5 (C1, C4, G3r, A1, M2): identical to 0.6.3 case for case, despite 9 releases in between. C1, C4 and M2 are cases the maintainer considers intended behavior; see the disclosure below |
| **15 cases:** adk-tracegauge | dev build of PR #91 (**not published**) | 6 | 9 (all flagged) | 0 |
| **15 cases:** adk-tracegauge | **`main` `921ac68`, the 0.10.0 candidate (not published)**, scored 2026-10-07 | 11 (G1, G1r, G3r, A1, M1 moved up from INCOMPLETE) | 4 (G2, G2r, G3, T1) | 0. Matches the outcome pre-registered before implementation. Scored after suite commit `72ca8da` (replay models named `gemini-*` now subclass ADK's `Gemini` so a tool can read the backend); the same build on the unmodified suite scored 8 / 7 / 0. See the scorecard's disclosure |
| **15 cases:** adk-tracegauge | **0.10.0 published (PyPI)**, scored 2026-10-07 | 11 (same as the candidate row above) | 4 (G2, G2r, G3, T1) | 0. Every case's dollar figure identical to the `921ac68` candidate scorecard; scored on the downloaded wheel, suite `79d93d7` (harness unchanged since `72ca8da`) |
| **15 cases:** adk-tracegauge | **0.10.1 published (PyPI)**, scored 2026-10-09 | 11 | 4 (G2, G2r, G3, T1) | 0. Identical to 0.10.0 case for case, dollar figures included, on google-adk 2.9.2 and 2.11.0; the shutdown handling it adds takes effect 2026-10-23, so the card is silent on that date onward. |

Verbatim outputs are in `scorecards/`; the earlier five-case pass/fail scorecards are kept there,
marked with the rule they used. A scorecard scores one version of each tool on these cases. It says nothing
about the parts the suite does not test (budget guards, exporters, dashboards, most providers); see
`docs/SCORING.md`.

**Which google-adk each scorecard is about.** The suite requires `google-adk>=2.6.0` with no upper bound (dropped
2026-10-05, matching adk-tracegauge 0.9.3: a cap goes stale within weeks and its only effect was pip downgrading
users). Every row above was scored on google-adk 2.9.2, with these re-runs on newer releases: adk-tracegauge 0.10.1
on 2.11.0 (2026-10-09), and both current releases, adk-tracegauge 0.10.1 and adk-finops 1.0.3, on 2.12.0
(2026-10-19) and on 2.13.0, the newest release at the time (2026-10-26). All of those re-runs are row for row
identical to the 2.9.2 scorecards, verdicts and dollar figures included
(`scorecards/2026-10-19_*_adk-2.12.0_15cases.md`, `scorecards/2026-10-26_*_adk-2.13.0_15cases.md`). The suite's own
32 tests and its reference adapter (15/15) pass on 2.10.0, 2.11.0, 2.12.0 and 2.13.0. The older tool versions in the table were not
re-scored on newer google-adk releases, so their rows are statements about 2.9.2.

**What was reported to adk-finops, and what was not.** On 2026-09-21 the adk-finops maintainer was sent three
issues with repros: **C1** (issue #1), **C4** (issue #2) and **C5** (issue #3). **A1, M2 and G3r are FAILs
that were never reported**, and neither were the INCOMPLETE cases (G1, G2, G1r, G2r, T1). See
`scorecards/README.md`.

## Disclosure: the author maintains one of the scored tools

**The author of this suite also maintains adk-tracegauge, one of the two tools scored.** That is a conflict
of interest, and a scorecard that ranks the author's own tool first should be read with it in mind. What is
done about it:

- **Every expected figure is hand-computed, with the arithmetic in the case's comment and in
  `arithmetic=`,** from one published rate set; none was produced by running either tool.
- **A reference plugin and a naive plugin are in the repo and tested.** The reference passes every case and
  the naive one fails each for the reason the case exists, so a case cannot be an artefact of one tool's
  quirks and the suite is provably satisfiable by code that is not adk-tracegauge.
- **The streaming fixture is a recording of a real Gemini stream**, and the one number that looked
  suspicious (19 vs 38 prompt tokens) was traced to its cause against the API itself
  (`docs/FIXTURE_PROVENANCE.md`).
- **The scoring rule is written down** (`docs/SCORING.md`), including the rule that the author's tool would
  fail too if it guessed: a guessed price for an unknown model fails.
- **Adapters read each tool's reported total.** Exception: the adk-finops adapter sums its tracker's private
  `_active_runs` attribute (the package has no public accessor) so that sub-agent sessions are counted; see
  `src/adk_cost_correctness/adapters/adk_finops.py`.
- **Only three of the failures were shown to the failing tool's maintainer before publication:** C1, C4 and
  C5 (adk-finops issues #1-#3, 2026-09-21, each with a minimal repro). **A1, M2 and G3r were not reported.**

**How the cases came about, with dates (all 2026-09-21).**
- **14:56 IST, commit `44daee8`: the original five cases (C1-C5) were written, and they were chosen post hoc:**
  after a hands-on comparison had shown where adk-finops fell short on them, and they are failure modes
  adk-tracegauge was built to handle. Under the first scoring rule (pass/fail) a tool that answers "unknown"
  could not lose.
- **15:50 IST, commit `a0b70d0`: counter-cases G1, G2, G3, T1, A1, M1, M2 were added, and the scoring became
  three outcomes (PASS / INCOMPLETE / FAIL),** to correct that. The counter-cases are drawn from what
  adk-finops does that adk-tracegauge does not (grounding fees; models such as gpt-4o) and from ADK features
  neither handles (audio, tool-use tokens). They were committed before either tool was scored on them, and no
  case or rule was changed after scoring. adk-tracegauge dropped below full marks on them (see the
  scorecard); adk-finops also dropped, on the original five.
- **After the first scoring (same day): the two adk-tracegauge findings that were silent wrong outputs (grounding fee omitted with no flag; audio priced at the text rate) were fixed in adk-tracegauge (#86, #87) and the tool was re-scored.** The fix flags them rather than pricing them, so those cases moved from FAIL / silent-INCOMPLETE to flagged-INCOMPLETE; no case or rule was changed, and the 0.8.1 scorecard is kept as scored. The adapter was changed to read the tool's own `total_is_complete` (see the scorecard header).

**What these mitigations do not fix: the choice of cases.** The five cases are failure modes adk-tracegauge
was built to handle, and they were chosen after the author had run a hands-on comparison and seen where
adk-finops fell short on them. The counter-cases reduce that bias but do not remove it: which counter-cases to write was still the
author's choice. The suite says nothing about what adk-finops does that adk-tracegauge does not outside
those (budget guards, exporters, a dashboard).

**Two of the failures are disputed by the maintainer, so they are contested scoring rules, not settled
defects.** The adk-finops owner closed both issues and described the behavior as intended (verbatim):

- Issue #1, C1 (a model with no published price is reported at the fallback rate), 2026-09-23T04:04:00Z: "We are
  not doing a pre-check whether model pricing is available or not, and output will reflect the tokens so user
  can calculate with the available price or better way is to register it with the package as mentioned
  [here](https://github.com/dmoonat/adk-finops/issues/1#issuecomment-5762512435)." The same mechanism produces
  the M2 FAIL (claude-opus-5), which was not reported separately.
- Issue #2, C4 (a doubly registered plugin counts every call twice), 2026-09-21T15:08:07Z: "This behavior is
  expected as adk-finops is a adk plugin." and, 2026-09-23T04:06:39Z: "Expected behavior, please check above
  [comment](https://github.com/dmoonat/adk-finops/issues/2#issuecomment-5762741336), thanks".

The suite's rule (`docs/SCORING.md`) is that a cost tool must not report a dollar figure for a model with no
published price, and must not silently double-count; adk-finops's maintainer disagrees. Read C1, C4 and M2
as "this suite's rule says FAIL", not as "a bug". Issue #3 (C5, streaming) was acknowledged and fixed.

None of that removes the conflict. Contest an adapter or a fixture by opening an issue with the arithmetic.

## Score your own plugin

Implement `CostPluginAdapter` (`src/adk_cost_correctness/adapters/base.py`): `start`, `plugins`,
`agent_kwargs`, `collect`. The adapter never sees the expected cost. `adapters/reference.py` is a 40-line
plugin that passes every case, and a naive one that fails each for the reason the case exists; the tests
prove both, so a scorecard cannot be an artefact of a badly written fixture.

Scoring rule: `docs/SCORING.md`.

## Licence

Apache-2.0 for the suite's own code and text (`LICENSE`, `NOTICE`). Third-party software it imports, the quoted
maintainer comments, the vendor price sources and the recorded fixture are inventoried in
`LICENSE-THIRD-PARTY`.
