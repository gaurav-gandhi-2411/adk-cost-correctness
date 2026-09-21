# Scorecard: adk-tracegauge 0.9.0, PUBLISHED wheel, 15 graded cases (with G1r-G3r)

Run 2026-09-21 against `adk-tracegauge==0.9.0` installed from PyPI (tag `v0.9.0` = `9da795c`), google-adk 2.9.2, suite commit `160507c` (the realistic twins G1r-G3r were committed BEFORE this run; no case or rule changed after). **G3r is FAIL and the reason matters:** the tool reported $0.0004344 with `total_is_complete: false` (the grounded sub-agent invocation carries tool-use tokens and is reported UNKNOWN by 0.9.0, so only the two root calls are priced; the report says the total EXCLUDES 1 unknown invocation and is at least that). The scoring rule as written gives FAIL to any figure that is not the expected figure or a declared incomplete figure, even when the tool flags it as a lower bound; that gap in the rule was NOT changed after seeing the result. See docs/SCORING.md.

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
G1r_grounding_gemini_2_5_real_shape counter   INCOMPLETE  a price is published ($0.0361907) but the tool flagged it unknown
G2r_grounding_gemini_3_real_shape counter   INCOMPLETE  a price is published ($0.0323050) but the tool flagged it unknown
G3r_grounding_via_agent_tool_real_shape counter   FAIL        expected $0.0371853, reported $0.0004344 (0.01x)
T1_tool_use_prompt_tokens      counter   INCOMPLETE  a price is published ($0.0023000) but the tool flagged it unknown
A1_audio_input                 counter   INCOMPLETE  $0.0003100 leaves out a component with a published price (expected $0.0013100, 0.24x)
M1_gpt_4o                      counter   INCOMPLETE  a price is published ($3.5000000) but the tool flagged it unknown
M2_claude_opus_5               counter   PASS        $7.5000000 matches

PASS 6 / INCOMPLETE 8 / FAIL 1 of 15 graded cases (sanity ok)
```
