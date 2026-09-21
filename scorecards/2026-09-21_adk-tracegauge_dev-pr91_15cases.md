# Scorecard: adk-tracegauge DEV build of PR #91 (tool-use tokens as an unpriced component), 15 graded cases -- NOT a published wheel

Run 2026-09-21 against the development build at adk-tracegauge commit `964cb7f` (branch `fix/tool-use-tokens-unpriced-component`, PR #91, unreleased; #89 already on main), suite commit `160507c`. This shows what 0.9.1 is expected to score; the PUBLISHED 0.9.1 must be scored again after release.

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
G1r_grounding_gemini_2_5_real_shape counter   INCOMPLETE  $0.0011907 leaves out a component with a published price (expected $0.0361907, 0.03x)
G2r_grounding_gemini_3_real_shape counter   INCOMPLETE  $0.0043050 leaves out a component with a published price (expected $0.0323050, 0.13x)
G3r_grounding_via_agent_tool_real_shape counter   INCOMPLETE  $0.0021853 leaves out a component with a published price (expected $0.0371853, 0.06x)
T1_tool_use_prompt_tokens      counter   INCOMPLETE  $0.0008000 leaves out a component with a published price (expected $0.0023000, 0.35x)
A1_audio_input                 counter   INCOMPLETE  $0.0003100 leaves out a component with a published price (expected $0.0013100, 0.24x)
M1_gpt_4o                      counter   INCOMPLETE  a price is published ($3.5000000) but the tool flagged it unknown
M2_claude_opus_5               counter   PASS        $7.5000000 matches

PASS 6 / INCOMPLETE 9 / FAIL 0 of 15 graded cases (sanity ok)
```
