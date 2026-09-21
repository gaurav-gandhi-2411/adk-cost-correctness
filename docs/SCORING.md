# Scoring rule

Every case ends in one of **three outcomes**:

| Outcome | Meaning |
|---|---|
| **PASS** | The correct figure; or "no figure" when no vendor publishes a price for the thing being priced. |
| **INCOMPLETE** | "Unknown", or a figure that omits a component, when the vendor DOES publish a price for it. An undercount that is missing something rather than wrong about something. |
| **FAIL** | Any other figure, including **any figure for a genuinely unpriceable component**, and a run that crashed instead of answering (except where refusing is the correct answer, C4). |

A tool that is never wrong but often incomplete is not "perfect": it ships numbers users cannot fully
trust as totals. A tool that always answers but is sometimes wrong is not "complete". The three-way split
keeps those two failures apart, so a fail-closed tool cannot look flawless by declining to answer, and a
tool that answers everything cannot hide its wrong figures behind coverage.

## How a figure is classified

Every expected figure is hand-computed in `src/adk_cost_correctness/cases.py`, from vendor prices read
from the vendor's own page (each case lists its sources and the date read).

1. Within **$0.0000005** of the expected figure -> PASS. (Some tools round each call to 7 decimals; that
   is not a defect.)
2. Within the same tolerance of a declared **incomplete figure** (the total with one published component
   left out: thinking tokens, cached tokens, a grounding fee, tool-use tokens, audio) -> INCOMPLETE. The
   scorecard says whether the tool flagged the omission or stayed silent; the outcome is the same.
3. No figure for a priced case (or the tool marked it unknown and reported nothing) -> INCOMPLETE.
4. Anything else -> FAIL. A component priced at the **wrong rate** is a wrong figure, not an omission
   (audio at the text rate, C-case A1, is FAIL).

## The unpriceable case (C1): a guess fails, even a close one

The fixture's model (`acme-llm-7b`) has no published price, so there is no correct figure to be near.
**Any figure reported for it FAILS** -- a fallback rate, a "similar model", a default, or $0.00 -- even if
it lands close and even if the tool also flags the model as unknown while still including the number.
PASS iff the tool reports no figure for the call. Reason: a cost tool's number is what people budget
against; "how close" depends on a model nobody can name, so the only honest output is "unknown".

This rule applies to genuinely unpriceable components ONLY. It is not a license to answer "unknown" for
something that has a published price: that is INCOMPLETE (rule 3), which is what the counter-cases test.

## Double registration (C4)

PASS iff the run is refused with an error, or the total equals a single count. FAIL at 2x.

## Streaming (C5)

Replays a real recorded Gemini stream (partials carry cumulative usage; the final response repeats the
last partial's). PASS iff the total is the price of one call.

## Grounding, tool-use tokens, audio, other vendors' models (G1-G3, T1, A1, M1, M2)

Grounding fees apply past a free allowance (Gemini 2.5: 1,500 prompts/day; Gemini 3.x: 5,000 requests per
month). A plugin cannot see an account's remaining allowance, so these cases price a request PAST the
allowance at the published paid rate. A tool that (reasonably) assumes the free tier reports the
"fee omitted" figure and scores INCOMPLETE; the suite does not claim that assumption is wrong for a given
user, only that it is not the fully priced answer.

G1 is ADK's real built-in `google_search`, which runs inside the model and fires no tool callbacks. G3 is
ADK's `GoogleSearchAgentTool`, the path on which a callback-based fee hook keyed on the tool name can fire.

### G1-G3 are not representative of real responses; G1r-G3r are (2026-09-21)

G1-G3 set no `tool_use_prompt_token_count`. Real Gemini 2.5 Google Search responses captured 2026-09-21
through ADK (6 of 6 grounded calls, adk-tracegauge repo `docs/design/data/real_grounding_2026-09-21.jsonl`)
always carry one (115-148 tokens). G1-G3 are kept **unchanged** (cases are not adjusted after scoring) but
they do not describe what a real grounded call looks like; read their results with that in mind. The twins
**G1r-G3r** use the token counts of those real captures (G1r: capture A; G3r: capture C, root and sub-agent
calls; G2r reuses the 2.5 counts because no Gemini 3.x grounded response could be captured with a free-tier
key, so its tool-use count is UNVERIFIED for 3.x).

Billing of tool-use tokens is not established (Vertex states Google Search grounding input tokens are not
charged; the Gemini API is UNVERIFIED; the URL-context docs bill theirs as input). So the twins accept two
figures as PASS, via `also_pass_usd`: tool-use tokens left out (the expected figure) or folded in at the
input rate. Anything else is FAIL, and the fee omitted (tokens only, either treatment) is INCOMPLETE. This
option exists only for those three cases.

## Harness sanity (S0)

A plain single call. Not graded; if a tool fails it the adapter or fixture is broken and the scorecard is
invalid (`adk-cost-correctness run` exits 2).

## Order of events (2026-09-21)

The original five cases (C1-C5) were written after the author had seen where one of the scored tools fell
short. The counter-cases and this three-outcome rule were written afterwards, and committed BEFORE the
tools were scored on them; the results were not consulted and no case or rule was changed after scoring.
See the README disclosure and `git log`.

## What the suite does not cover

Other providers beyond gpt-4o and claude-opus-5, long-context tiers, promo windows, Batch/Flex tiers,
explicit-cache storage fees (billed on cache lifetime, not derivable from per-call usage), budget guards,
exporters, dashboards. Absence from this suite is not a claim of correctness.

## Scorer changelog

Each entry names what the scorer did wrong, when it was found relative to results, and whether the rule text
changed. The rule text above has not been edited by any entry.

- **2026-09-21 -- scorer bug: a declared lower bound scored FAIL.** The rule as written says a figure that
  omits a component, or a component reported unknown, when the vendor publishes a price, is INCOMPLETE. The
  scorer only recognised a total as such when it equalled one of a case's pre-computed partial figures
  (`incomplete_usd`) or when no figure was reported. On G3r, published adk-tracegauge 0.9.0 priced the two
  root calls ($0.0004344), reported the grounded sub-agent invocation UNKNOWN and said the total excludes it;
  that matches the written rule, but the figure equalled no pre-computed partial, so the scorer returned
  FAIL. **The fix was made after seeing this result.** The scorer now scores a figure the tool has flagged
  as leaving something out (`Outcome.flagged`) and that is below the expected figure as INCOMPLETE ("declared
  lower bound"). A figure that is not flagged, or is above the expected one, still falls through to FAIL, and
  a flagged figure equal to the expected one still passes. **The rule text was not changed** (this is the
  scorer implementing it as already written). Test: `test_a_declared_lower_bound_is_incomplete_but_an_undeclared_wrong_figure_still_fails`.
  Effect on published results, by re-scoring both tools: see `scorecards/`.
