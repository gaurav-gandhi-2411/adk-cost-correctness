# Scorecard: adk-finops (three-outcome rule, 12 graded cases)

Run twice on 2026-09-21 (identical results), after the cases and the rule were committed (`a0b70d0`); google-adk 2.9.2, Python 3.11, `adk-cost-correctness run --adapter adk-finops`. Verbatim output:

```
Scorecard: adk-finops 0.6.1
case                           origin    result      detail
S0_sanity                      original  PASS        $0.0008000 matches
C1_unknown_model               original  FAIL        priced a model with no published price: reported $0.5500000 (not flagged as unknown) -- any figure is a guess
C2_cached_tokens               original  PASS        $0.0010900 matches
C3_thinking_tokens             original  PASS        $0.0030500 matches
C4_double_registration         original  FAIL        expected $0.0008000, reported $0.0016000 (2.00x)
C5_streaming_partials          original  FAIL        expected $0.0005239, reported $0.0020673 (3.95x)
G1_grounding_gemini_2_5        counter   INCOMPLETE  $0.0013500 leaves out a component with a published price (expected $0.0363500, 0.04x, not flagged as incomplete)
G2_grounding_gemini_3          counter   INCOMPLETE  $0.0057000 leaves out a component with a published price (expected $0.0477000, 0.12x, not flagged as incomplete)
G3_grounding_via_agent_tool    counter   PASS        $0.0255800 matches
T1_tool_use_prompt_tokens      counter   INCOMPLETE  $0.0008000 leaves out a component with a published price (expected $0.0023000, 0.35x, not flagged as incomplete)
A1_audio_input                 counter   FAIL        expected $0.0013100, reported $0.0006100 (0.47x)
M1_gpt_4o                      counter   PASS        $3.5000000 matches
M2_claude_opus_5               counter   FAIL        expected $7.5000000, reported $0.5500000 (0.07x)

PASS 4 / INCOMPLETE 3 / FAIL 5 of 12 graded cases (sanity ok)
```
