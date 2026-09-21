# adk-cost-correctness

A tool-agnostic correctness suite for Google ADK cost-tracking plugins. Five cases where cost tools
commonly go wrong, each a deterministic fixture with a hand-computed expected cost; any plugin can be
scored by writing one small adapter.

| Case | What it checks |
|---|---|
| C1 unknown model | A model with no published price is reported as unknown, not priced. A guess fails, even a close one. |
| C2 cached tokens | The cached part of the prompt is billed at the cached rate. |
| C3 thinking tokens | Thinking tokens are counted and billed as output. |
| C4 double registration | The same plugin registered twice does not double the cost silently. |
| C5 streaming partials | Cumulative usage on every streamed chunk is priced once. Replayed from a real Gemini stream. |

## Run it

```bash
pip install -e ".[adk-tracegauge,adk-finops]"
adk-cost-correctness run --adapter adk-tracegauge
adk-cost-correctness run --adapter adk-finops
```

No API key and no network: the model is a deterministic replay behind a real `InMemoryRunner`.

## Scorecards (2026-09-21, google-adk 2.9.2)

| Tool | Version | Passed |
|---|---|---|
| adk-tracegauge | 0.8.1 | 5/5 |
| adk-finops | 0.6.1 (commit `69ed257`) | 2/5 (fails C1, C4, C5) |

Verbatim outputs are in `scorecards/`. They score one version of each tool on five cases. They say
nothing about the parts of either tool the suite does not test (budget guards, exporters, dashboards,
other providers), see `docs/SCORING.md`. The three adk-finops failures were reported to its maintainers on
2026-09-21 with repros; see `scorecards/README.md`.

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

**What these mitigations do not fix: the choice of cases.** The five cases are failure modes adk-tracegauge
was built to handle, and they were chosen after the author had run a hands-on comparison and seen where
adk-finops fell short on them. So the suite favours the author's tool by construction, and says nothing about
what adk-finops does that adk-tracegauge does not (budget guards, exporters, a dashboard, non-Google models).

None of that removes the conflict. Contest an adapter or a fixture by opening an issue with the arithmetic.

## Score your own plugin

Implement `CostPluginAdapter` (`src/adk_cost_correctness/adapters/base.py`): `start`, `plugins`,
`agent_kwargs`, `collect`. The adapter never sees the expected cost. `adapters/reference.py` is a 40-line
plugin that passes every case, and a naive one that fails each for the reason the case exists; the tests
prove both, so a scorecard cannot be an artefact of a badly written fixture.

Scoring rule: `docs/SCORING.md`.
