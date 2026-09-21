# Scorecard: adk-tracegauge (three-outcome rule, 12 graded cases)

Run twice on 2026-09-21 (identical results), after the cases and the rule were committed (`a0b70d0`); google-adk 2.9.2, Python 3.11, `adk-cost-correctness run --adapter adk-tracegauge`. Verbatim output:

```
Scorecard: adk-tracegauge 0.8.1
case                           origin    result      detail
S0_sanity                      original  PASS        $0.0008000 matches
C1_unknown_model               original  PASS        reported no price (flagged unknown)
C2_cached_tokens               original  PASS        $0.0010900 matches
C3_thinking_tokens             original  PASS        $0.0030500 matches
C4_double_registration         original  PASS        refused the second registration (DoubleRegistrationError: adk_tracegauge: TraceGaugeUsagePlug...) and holds a single-count figure: $0.0008000
C5_streaming_partials          original  PASS        $0.0005239 matches
G1_grounding_gemini_2_5        counter   INCOMPLETE  $0.0013500 leaves out a component with a published price (expected $0.0363500, 0.04x, not flagged as incomplete)
G2_grounding_gemini_3          counter   INCOMPLETE  $0.0057000 leaves out a component with a published price (expected $0.0477000, 0.12x, not flagged as incomplete)
G3_grounding_via_agent_tool    counter   INCOMPLETE  $0.0115800 leaves out a component with a published price (expected $0.0255800, 0.45x, not flagged as incomplete)
T1_tool_use_prompt_tokens      counter   INCOMPLETE  a price is published ($0.0023000) but the tool flagged it unknown
A1_audio_input                 counter   FAIL        expected $0.0013100, reported $0.0006100 (0.47x)
M1_gpt_4o                      counter   INCOMPLETE  a price is published ($3.5000000) but the tool flagged it unknown
M2_claude_opus_5               counter   PASS        $7.5000000 matches

PASS 6 / INCOMPLETE 5 / FAIL 1 of 12 graded cases (sanity ok)
```
