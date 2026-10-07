# Scorecard: adk-tracegauge main `921ac68` (the 0.10.0 candidate, NOT published), 15 graded cases

Run 2026-10-07 against adk-tracegauge `main` at `921ac68` (all five 0.10.0 pricing PRs merged: #107, #109, #110, #111, #112; the version string still reads 0.9.3 because the bump PR is not merged), google-adk 2.9.2, suite at `72ca8da`. Cases and scoring rule unchanged. Expected outcome pre-registered before implementation in adk-tracegauge `docs/design/pricing-gaps-0-10-0-preregistration.md` (PR #106): 11 PASS / 4 INCOMPLETE (G2, G3, G2r, T1) / 0 FAIL. **Result matches it.**

```
Scorecard: adk-tracegauge 0.9.3
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

Against the published 0.9.1 scorecard (`2026-09-21_adk-tracegauge_0.9.1-published_15cases.md`, 6 PASS / 9 INCOMPLETE / 0 FAIL): no case regressed. G1, G1r, G3r, A1 and M1 moved INCOMPLETE -> PASS; the nine cases that passed before still pass; G2, G2r, G3 (Gemini 3.x grounding) and T1 (URL-context tool-use tokens) stay INCOMPLETE.

## Disclosure: a suite change made while this build was being scored

The suite's replay model was a bare `BaseLlm` with no `api_client`, so a tool that prices a grounding fee only after positively reading that the Gemini API served the call could not be scored on grounding at all. Suite commit `72ca8da` makes `gemini-*` replay models subclass ADK's own `Gemini` class (client built offline from a placeholder key). Checked before committing, on the same harness: adk-tracegauge 0.9.1 still scores 6 / 9 / 0 and adk-finops 0.6.1 still 4 / 5 / 6, both identical to their recorded scorecards.

The same build against the UNMODIFIED suite (`eac41ec`), recorded first and before the change was made (tool tree = the final tree before squash-merge, not `921ac68` itself):

```
Scorecard: adk-tracegauge 0.9.3
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
A1_audio_input                 counter   PASS        $0.0013100 matches
M1_gpt_4o                      counter   PASS        $3.5000000 matches
M2_claude_opus_5               counter   PASS        $7.5000000 matches

PASS 8 / INCOMPLETE 7 / FAIL 0 of 15 graded cases (sanity ok)
```

That is 8 PASS / 7 INCOMPLETE / 0 FAIL: A1 and M1 pass, every grounding case stays flagged because the backend cannot be read. The author maintains this tool; see the disclosure in the README.
