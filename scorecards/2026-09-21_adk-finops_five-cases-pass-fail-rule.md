# Scorecard: adk-finops

Run 2026-09-21 with google-adk 2.9.2, Python 3.11, `adk-cost-correctness run --adapter adk-finops`. Verbatim output:

```
Scorecard: adk-finops 0.6.1
case                       result detail
S0_sanity                  PASS   $0.0008000 matches
C1_unknown_model           FAIL   priced a model with no published price: reported $0.5500000 (not flagged as unknown) -- any figure is a guess
C2_cached_tokens           PASS   $0.0010900 matches
C3_thinking_tokens         PASS   $0.0030500 matches
C4_double_registration     FAIL   expected $0.0008000, reported $0.0016000 (2.00x)
C5_streaming_partials      FAIL   expected $0.0005239, reported $0.0020673 (3.95x)

2/5 graded cases passed (sanity ok); streaming fixture verified on a real stream: True
```
