# Scorecard: adk-tracegauge 0.9.0, patched build (three-outcome rule, 12 graded cases)

Run 2026-09-21 on adk-tracegauge `main` at `9da795c` (0.9.0, not yet released to PyPI; contains #86 grounding flag and #87 audio / non-text-output flag), installed from that commit; google-adk 2.9.2, Python 3.11, `adk-cost-correctness run --adapter adk-tracegauge`. Cases and scoring rule are unchanged since `a0b70d0`. **One suite change was made after the 0.8.1 scorecard, and it is disclosed here:** the adk-tracegauge adapter now reads the tool's own `report --json` fields (`total_usd_priced`, `total_is_complete`) instead of `bool(snapshot.skipped)`, because 0.9.0 introduces a second kind of "incomplete" (a priced invocation with an unpriced component). For 0.8.1 the two definitions coincide (its `total_is_complete` was `not skipped`), so the 0.8.1 scorecard stands as recorded.

The output below carries no "not flagged as incomplete" note on G1-G3 or A1 because the tool now reports `total_is_complete: false` for them (the scoring code adds that note only for a silent omission).

```
Scorecard: adk-tracegauge 0.9.0
case                           origin    result      detail
S0_sanity                      original  PASS        $0.0008000 matches
C1_unknown_model               original  PASS        reported no price (flagged unknown)
C2_cached_tokens               original  PASS        $0.0010900 matches
C3_thinking_tokens             original  PASS        $0.0030500 matches
C4_double_registration         original  PASS        refused the second registration (DoubleRegistrationError: adk_tracegauge: TraceGaugeUsagePlug...) and holds a single-count figure: $0.0008000
C5_streaming_partials          original  PASS        $0.0005239 matches
G1_grounding_gemini_2_5        counter   INCOMPLETE  $0.0013500 leaves out a component with a published price (expected $0.0363500, 0.04x)
G2_grounding_gemini_3          counter   INCOMPLETE  $0.0057000 leaves out a component with a published price (expected $0.0477000, 0.12x)
G3_grounding_via_agent_tool    counter   INCOMPLETE  $0.0115800 leaves out a component with a published price (expected $0.0255800, 0.45x)
T1_tool_use_prompt_tokens      counter   INCOMPLETE  a price is published ($0.0023000) but the tool flagged it unknown
A1_audio_input                 counter   INCOMPLETE  $0.0003100 leaves out a component with a published price (expected $0.0013100, 0.24x)
M1_gpt_4o                      counter   INCOMPLETE  a price is published ($3.5000000) but the tool flagged it unknown
M2_claude_opus_5               counter   PASS        $7.5000000 matches

PASS 6 / INCOMPLETE 6 / FAIL 0 of 12 graded cases (sanity ok)
```
