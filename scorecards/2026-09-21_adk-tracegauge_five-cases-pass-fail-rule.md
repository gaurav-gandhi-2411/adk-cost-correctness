# Scorecard: adk-tracegauge

Run 2026-09-21 with google-adk 2.9.2, Python 3.11, `adk-cost-correctness run --adapter adk-tracegauge`. Verbatim output:

```
Scorecard: adk-tracegauge 0.8.1
case                       result detail
S0_sanity                  PASS   $0.0008000 matches
C1_unknown_model           PASS   reported no price (flagged unknown)
C2_cached_tokens           PASS   $0.0010900 matches
C3_thinking_tokens         PASS   $0.0030500 matches
C4_double_registration     PASS   refused the second registration (DoubleRegistrationError: adk_tracegauge: TraceGaugeUsagePlug...) and holds a single-count figure: $0.0008000
C5_streaming_partials      PASS   $0.0005239 matches

5/5 graded cases passed (sanity ok); streaming fixture verified on a real stream: True
```
