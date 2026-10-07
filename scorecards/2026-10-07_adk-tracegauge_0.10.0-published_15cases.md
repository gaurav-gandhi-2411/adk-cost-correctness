# Scorecard: adk-tracegauge 0.10.0, PUBLISHED wheel, 15 graded cases

Run 2026-10-07 against `adk-tracegauge==0.10.0` installed from PyPI (uploaded 2026-10-07T18:06:26Z; tag `v0.10.0` = `c43bb96`, release run 37643558428), google-adk 2.9.2, suite at `79d93d7` (harness identical to `72ca8da`). Cases and scoring rule unchanged. Run about 20 minutes after upload, in a clean venv (`pip install google-adk==2.9.2`, the suite editable, then `pip install adk-tracegauge==0.10.0`; `adk_tracegauge.__file__` resolved inside that venv's site-packages).

**Result: 11 PASS / 4 INCOMPLETE / 0 FAIL, case for case identical to the candidate scorecard `2026-10-07_adk-tracegauge_main-921ac68_0.10.0-candidate_15cases.md`** (same dollar figures on every case) and equal to the outcome pre-registered in adk-tracegauge PR #106. No case regressed against 0.9.1 (6 / 9 / 0). The traceback text a run prints above the scorecard is C4's intended `DoubleRegistrationError`.

```
Scorecard: adk-tracegauge 0.10.0
case                           origin    result      detail
S0_sanity                      original  PASS        $0.0008000 matches
C1_unknown_model               original  PASS        reported no price (flagged unknown)
C2_cached_tokens               original  PASS        $0.0010900 matches
C3_thinking_tokens             original  PASS        $0.0030500 matches
C4_double_registration         original  PASS        refused the second registration (DoubleRegistrationError: adk_tracegauge: TraceGaugeUsagePlug...) and holds a single-count figure: $0.0008000
C5_streaming_partials          original  PASS        $0.0005239 matches
G1_grounding_gemini_2_5        counter   PASS        $0.0363500 matches
G2_grounding_gemini_3          counter   INCOMPLETE  $0.0057000 leaves out a component with a published price (expected $0.0477000, 0.12x)
G3_grounding_via_agent_tool    counter   INCOMPLETE  $0.0115800 leaves out a component with a published price (expected $0.0255800, 0.45x)
G1r_grounding_gemini_2_5_real_shape counter   PASS        $0.0362264 matches an accepted alternative (expected $0.0361907; the case's billing of one component is not established)
G2r_grounding_gemini_3_real_shape counter   INCOMPLETE  $0.0043050 leaves out a component with a published price (expected $0.0323050, 0.13x)
G3r_grounding_via_agent_tool_real_shape counter   PASS        $0.0372249 matches an accepted alternative (expected $0.0371853; the case's billing of one component is not established)
T1_tool_use_prompt_tokens      counter   INCOMPLETE  $0.0008000 leaves out a component with a published price (expected $0.0023000, 0.35x)
A1_audio_input                 counter   PASS        $0.0013100 matches
M1_gpt_4o                      counter   PASS        $3.5000000 matches
M2_claude_opus_5               counter   PASS        $7.5000000 matches

PASS 11 / INCOMPLETE 4 / FAIL 0 of 15 graded cases (sanity ok)
```
