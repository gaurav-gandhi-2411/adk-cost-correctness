# Scoring rule

A case is **PASS** or **FAIL**. There is no partial credit and no "close enough" outside the tolerance
below. Every expected figure is hand-computed in `src/adk_cost_correctness/cases.py`, from one rate
set (Gemini Developer API, `gemini-2.5-flash`: $0.30 in, $2.50 out, $0.03 cached, per 1M tokens).

## Cases that have a correct dollar figure (S0, C2, C3, C5)

PASS iff the tool reports a total within **$0.0000005** of the expected figure. That tolerance is only
there because some tools round each call to 7 decimals. A tool that reports no figure, or raises,
FAILS.

## The unknown-model case (C1): a guess fails, even a close one

The fixture's model (`acme-llm-7b`) has no published price, so there is no correct figure to be near.
**A tool that reports ANY dollar figure for it FAILS** -- a $0.30/$2.50 fallback, a "similar model"
rate, a default, or $0.00. It fails even if the figure happens to be close to what some real model would
cost, and even if the tool also flags the model as unknown while still including the number.

PASS iff the tool reports no figure for the call: it marks it unknown, excludes it from its total, or
refuses to continue. Reason: a cost tool's number is what people budget against. A wrong number that is
labelled as an estimate elsewhere in the UI is still the number that gets used, and "how close" depends on
a model nobody can name, so the only honest output is "unknown". The fixture would be pointless if
closeness could rescue it: a fallback that lands within 1% on this fixture would be wrong by 10x on the
next model.

## Double registration (C4)

The same plugin is registered twice on one agent (the plugin and its own callback). PASS iff the run is
refused with an error, or the total equals a **single** count. FAIL at 2x (or anything else).

## Streaming (C5)

Replays a real recorded stream (`data/real_stream_gemini-2.5-flash_2026-09-21.json`): six partial chunks
with cumulative usage, then a final response with the same usage as the last chunk. PASS iff the total is
the price of one call. This case is graded only because the assumption behind it -- that partials carry
cumulative usage -- was verified against a real stream on 2026-09-21 (see the fixture's `_provenance`).

## Harness sanity (S0)

A plain single call. It is not graded; if a tool fails it, the adapter or the fixture is broken and the
scorecard is invalid (`adk-cost-correctness run` exits 2).

## What the suite does not cover

Other providers' pricing, long-context tiers, promo windows, grounding/tool fees, multi-agent rollup,
Batch/Flex tiers, budget guards, exporters. Absence from this suite is not a claim of correctness.
