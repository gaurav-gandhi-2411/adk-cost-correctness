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
other providers), see `docs/SCORING.md`. The suite's author maintains adk-tracegauge; the fixtures and
the scoring rule are public so the result can be checked or the adapter contested.

## Score your own plugin

Implement `CostPluginAdapter` (`src/adk_cost_correctness/adapters/base.py`): `start`, `plugins`,
`agent_kwargs`, `collect`. The adapter never sees the expected cost. `adapters/reference.py` is a 40-line
plugin that passes every case, and a naive one that fails each for the reason the case exists; the tests
prove both, so a scorecard cannot be an artefact of a badly written fixture.

Scoring rule: `docs/SCORING.md`.
