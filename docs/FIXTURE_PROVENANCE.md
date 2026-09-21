# Fixture provenance: where C5's numbers come from

C5 replays a real streamed call (`src/adk_cost_correctness/data/real_stream_gemini-2.5-flash_2026-09-21.json`)
and expects the price of ONE call at ADK's reported `prompt_token_count` of **38**. A raw google-genai call
on the same prompt had reported 19. This page records why those differ, because if ADK reported more tokens
than the API bills for the same request, the expected value (and both scorecards) would be wrong.

## What differs: a different request, not double counting

Captured 2026-09-21 with a `before_model_callback` on the same agent that produced the fixture (ADK 2.9.2,
`gemini-2.5-flash`, Gemini Developer API):

```
system_instruction: "Answer briefly.\n\nYou are an agent. Your internal name is \"root_agent\"."
contents:           [{"role": "user", "parts": [{"text": "List five European capital cities, one per line, each with a one-sentence fact."}]}]
config:             max_output_tokens=300, thinking_budget=0
```

ADK prepends its own line ("You are an agent. Your internal name is ...") to the agent's `instruction`. The
earlier raw call had no system instruction at all, so it was a smaller request.

## The numbers, same session

| Request | Endpoint | Tokens |
|---|---|---|
| ADK's exact request (contents + system_instruction + config) | ADK `after_model_callback`, every streamed response | **38** |
| The identical request | raw google-genai `generate_content_stream`, last chunk's `usage_metadata` | **38** |
| The bare user prompt, no system instruction | raw google-genai streaming | 19 |
| The bare user prompt | `count_tokens` (SDK) | 19 |
| The identical request | `count_tokens` with `system_instruction` (SDK) | not available: the SDK raises "system_instruction parameter is only supported in Gemini Enterprise Agent Platform mode" |
| The identical request | REST `models/gemini-2.5-flash:countTokens` with `generateContentRequest` | **37** |

**Verdict:** ADK's 38 equals what the API itself reports for the identical request, so C5's expected value
(38 in, 205 out = $0.0005239) is correct and needs no change; neither tool's input is inflated by ADK.

## One unexplained token

The REST `countTokens` estimate for the full request is 37, one less than the 38 that generation reports
for it. With no system instruction the two agree (19 = 19). Why the two endpoints differ by one token for a
request with a system instruction was not investigated (UNVERIFIED). The generation-time figure is the one
`usage_metadata` carries and the one a plugin can read, so the suite uses it.

## Limits

One model, one prompt, one API (Gemini Developer API), one day. The stream's candidate counts vary from run
to run (205 in the fixture; 218, 208 and 137 in the other runs made that day), which is why the fixture replays a recording instead
of calling the API.
