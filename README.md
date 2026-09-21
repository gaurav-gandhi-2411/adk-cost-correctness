# adk-cost-correctness

A tool-agnostic correctness suite for Google ADK cost-tracking plugins: twelve deterministic cases with
hand-computed expected costs and vendor-sourced prices, scored PASS / INCOMPLETE / FAIL. Any plugin can be
scored by writing one small adapter.

| Case | What it checks | Added |
|---|---|---|
| C1 unknown model | A model with no published price is reported as unknown, not priced. A guess fails, even a close one. | original five |
| C2 cached tokens | The cached part of the prompt is billed at the cached rate. | original five |
| C3 thinking tokens | Thinking tokens are counted and billed as output. | original five |
| C4 double registration | The same plugin registered twice does not double the cost silently. | original five |
| C5 streaming partials | Cumulative usage on every streamed chunk is priced once. Replayed from a real Gemini stream. | original five |
| G1 / G2 | Google Search grounding fee, Gemini 2.5 (per grounded prompt) and Gemini 3.x (per query), ADK's built-in tool. | counter-case |
| G3 | The same fee through ADK's `GoogleSearchAgentTool` (the path a tool-callback fee hook can fire on). | counter-case |
| T1 | Tokens fetched by a built-in tool (URL context) are billed as input. | counter-case |
| A1 | Audio input tokens have their own, higher rate. | counter-case |
| M1 / M2 | A published price for a model outside a tool's table: gpt-4o, claude-opus-5. | counter-case |

Each case ends **PASS**, **INCOMPLETE** (unknown or omitted where a price is published) or **FAIL** (a wrong
figure, or any guess for an unpriceable component); see `docs/SCORING.md`.

## Run it

```bash
pip install -e ".[adk-tracegauge,adk-finops]"
adk-cost-correctness run --adapter adk-tracegauge
adk-cost-correctness run --adapter adk-finops
```

No API key and no network: the model is a deterministic replay behind a real `InMemoryRunner`.

## Scorecards (2026-09-21, google-adk 2.9.2, 12 graded cases)

| Tool | Version | PASS | INCOMPLETE | FAIL |
|---|---|---|---|---|
| adk-tracegauge | 0.8.1 | 6 | 5 (G1, G2, G3, T1, M1) | 1 (A1 audio) |
| adk-finops | 0.6.1 (commit `69ed257`) | 4 | 3 (G1, G2, T1) | 5 (C1, C4, C5, A1, M2) |

Verbatim outputs are in `scorecards/`; the earlier five-case pass/fail scorecards are kept there,
marked with the rule they used. A scorecard scores one version of each tool on these cases. It says nothing
about the parts the suite does not test (budget guards, exporters, dashboards, most providers); see
`docs/SCORING.md`. The three adk-finops failures found by the original five cases were reported to its
maintainers on 2026-09-21 with repros; see `scorecards/README.md`.

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
- **Adapters read each tool the way its users see it,** and the failing tool's maintainers were shown each
  failure with a minimal repro before anything was published.

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

**What these mitigations do not fix: the choice of cases.** The five cases are failure modes adk-tracegauge
was built to handle, and they were chosen after the author had run a hands-on comparison and seen where
adk-finops fell short on them. The counter-cases reduce that bias but do not remove it: which counter-cases to write was still the
author's choice. The suite says nothing about what adk-finops does that adk-tracegauge does not outside
those (budget guards, exporters, a dashboard).

None of that removes the conflict. Contest an adapter or a fixture by opening an issue with the arithmetic.

## Score your own plugin

Implement `CostPluginAdapter` (`src/adk_cost_correctness/adapters/base.py`): `start`, `plugins`,
`agent_kwargs`, `collect`. The adapter never sees the expected cost. `adapters/reference.py` is a 40-line
plugin that passes every case, and a naive one that fails each for the reason the case exists; the tests
prove both, so a scorecard cannot be an artefact of a badly written fixture.

Scoring rule: `docs/SCORING.md`.
