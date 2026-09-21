"""The suite must be satisfiable (the reference plugin passes everything) and must discriminate (the
naive plugin does not). Scoring rules are unit-tested with synthetic outcomes, including "a close guess
still fails" and the three-way PASS / INCOMPLETE / FAIL split."""

from __future__ import annotations

import pytest

from adk_cost_correctness.adapters.reference import NaiveAdapter, ReferenceAdapter
from adk_cost_correctness.cases import Case, all_cases
from adk_cost_correctness.harness import run_all
from adk_cost_correctness.scoring import Outcome, score


def _case(case_id: str) -> Case:
    return next(c for c in all_cases() if c.id == case_id)


def _v(case_id: str, **outcome: object) -> str:
    return score(_case(case_id), Outcome(**outcome)).verdict  # type: ignore[arg-type]


# --- scoring rules, no ADK involved --------------------------------------------------------------


def test_a_close_guess_for_an_unknown_model_fails():
    s = score(_case("C1_unknown_model"), Outcome(total_usd=0.55))
    assert s.verdict == "FAIL" and "guess" in s.reason


def test_zero_or_a_flagged_figure_is_also_a_guess_for_an_unknown_model():
    assert _v("C1_unknown_model", total_usd=0.0) == "FAIL"
    assert _v("C1_unknown_model", total_usd=0.55, flagged=True) == "FAIL"


def test_no_figure_passes_an_unknown_model_however_it_is_reported():
    assert _v("C1_unknown_model", total_usd=None, flagged=True) == "PASS"
    assert _v("C1_unknown_model", total_usd=None, refused="ValueError: x") == "PASS"


def test_the_expected_figure_within_half_a_microdollar_passes():
    assert _v("C2_cached_tokens", total_usd=0.00109) == "PASS"
    assert _v("C2_cached_tokens", total_usd=0.0010904) == "PASS"  # per-call rounding to 7 decimals


def test_a_figure_that_leaves_out_a_published_component_is_incomplete_not_fail():
    assert _v("C3_thinking_tokens", total_usd=0.00055) == "INCOMPLETE"  # thinking tokens dropped
    assert _v("C2_cached_tokens", total_usd=0.00085) == "INCOMPLETE"  # cached tokens dropped
    assert _v("G1_grounding_gemini_2_5", total_usd=0.00135) == "INCOMPLETE"  # grounding fee dropped
    assert _v("T1_tool_use_prompt_tokens", total_usd=0.0008) == "INCOMPLETE"


def test_no_figure_for_a_priceable_case_is_incomplete_whether_or_not_it_is_flagged():
    assert _v("M1_gpt_4o", total_usd=None, flagged=True) == "INCOMPLETE"
    assert _v("M1_gpt_4o", total_usd=None) == "INCOMPLETE"


def test_any_other_figure_is_a_fail():
    assert (
        _v("C2_cached_tokens", total_usd=0.0011) == "FAIL"
    )  # near, but not the figure or a partial
    assert _v("M2_claude_opus_5", total_usd=0.55) == "FAIL"  # a fallback guess for a priced model
    assert (
        _v("A1_audio_input", total_usd=0.00061) == "FAIL"
    )  # audio at the text rate: wrong, not omitted


def test_the_realistic_twins_accept_tool_use_tokens_left_out_or_folded_in_at_the_input_rate():
    for case_id, expected, folded in [
        ("G1r_grounding_gemini_2_5_real_shape", 0.0361907, 0.0362264),
        ("G2r_grounding_gemini_3_real_shape", 0.032305, 0.0324835),
        ("G3r_grounding_via_agent_tool_real_shape", 0.0371853, 0.0372249),
    ]:
        assert _v(case_id, total_usd=expected) == "PASS"
        assert _v(case_id, total_usd=folded) == "PASS"  # billing of tool-use tokens not established
        assert (
            _v(case_id, total_usd=expected + 0.0001) == "FAIL"
        )  # near, but neither accepted figure
    # the fee omitted (tokens only, either treatment) is INCOMPLETE, not PASS
    assert _v("G1r_grounding_gemini_2_5_real_shape", total_usd=0.0011907) == "INCOMPLETE"
    assert _v("G1r_grounding_gemini_2_5_real_shape", total_usd=0.0012264) == "INCOMPLETE"
    # no figure at all (the invocation reported unknown) is INCOMPLETE
    assert (
        _v("G3r_grounding_via_agent_tool_real_shape", total_usd=None, flagged=True) == "INCOMPLETE"
    )


def test_the_original_grounding_cases_are_not_accepting_alternatives():
    # G1-G3 carry no tool-use tokens; also_pass_usd is only for the real-shape twins.
    for case_id in (
        "G1_grounding_gemini_2_5",
        "G2_grounding_gemini_3",
        "G3_grounding_via_agent_tool",
    ):
        assert _case(case_id).also_pass_usd == ()
        assert _case(case_id).step.tool_use_prompt == 0


def test_crashing_instead_of_answering_is_a_fail():
    assert _v("C3_thinking_tokens", total_usd=None, refused="RuntimeError: boom") == "FAIL"


def test_double_registration_passes_by_counting_once_or_by_refusing_and_fails_at_2x():
    assert _v("C4_double_registration", total_usd=0.0008) == "PASS"
    assert _v("C4_double_registration", total_usd=None, refused="DoubleRegistrationError") == "PASS"
    twice = score(_case("C4_double_registration"), Outcome(total_usd=0.0016))
    assert twice.verdict == "FAIL" and "2.00x" in twice.reason


# --- the fixtures' own arithmetic ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("S0_sanity", 0.0008),
        ("C2_cached_tokens", 0.00109),
        ("C3_thinking_tokens", 0.00305),
        ("C4_double_registration", 0.0008),
        ("C5_streaming_partials", 0.0005239),  # 38 in + 205 out, from the real recorded stream
        ("G1_grounding_gemini_2_5", 0.03635),  # $0.00135 tokens + $0.035 (one grounded prompt)
        ("G2_grounding_gemini_3", 0.0477),  # $0.0057 tokens + 3 x $0.014
        ("G3_grounding_via_agent_tool", 0.02558),  # $0.01158 tokens + 1 x $0.014
        ("G1r_grounding_gemini_2_5_real_shape", 0.0361907),  # $0.0011907 + $0.035
        ("G2r_grounding_gemini_3_real_shape", 0.032305),  # $0.004305 + 2 x $0.014
        ("G3r_grounding_via_agent_tool_real_shape", 0.0371853),  # $0.0021853 + $0.035
        ("T1_tool_use_prompt_tokens", 0.0023),  # (1,000 + 5,000) x $0.30/M + 200 x $2.50/M
        ("A1_audio_input", 0.00131),  # 200 text + 1,000 audio + 100 out
        ("M1_gpt_4o", 3.5),
        ("M2_claude_opus_5", 7.5),
    ],
)
def test_expected_costs_match_the_hand_arithmetic_in_the_case_comments(case_id, expected):
    assert _case(case_id).expected_usd == pytest.approx(expected, abs=1e-9)


def test_every_priced_case_names_its_vendor_source_and_the_case_origin_is_recorded():
    cases = all_cases()
    assert all(c.sources for c in cases if c.kind != "unpriced")
    originals = {c.id for c in cases if c.origin == "original"}
    assert originals == {
        "S0_sanity",
        "C1_unknown_model",
        "C2_cached_tokens",
        "C3_thinking_tokens",
        "C4_double_registration",
        "C5_streaming_partials",
    }
    assert {c.id for c in cases if c.origin == "counter"} == {
        "G1_grounding_gemini_2_5",
        "G2_grounding_gemini_3",
        "G3_grounding_via_agent_tool",
        "G1r_grounding_gemini_2_5_real_shape",
        "G2r_grounding_gemini_3_real_shape",
        "G3r_grounding_via_agent_tool_real_shape",
        "T1_tool_use_prompt_tokens",
        "A1_audio_input",
        "M1_gpt_4o",
        "M2_claude_opus_5",
    }


def test_the_streaming_fixture_is_the_recorded_real_stream():
    step = _case("C5_streaming_partials").step
    assert step.partial_outputs == (4, 22, 71, 120, 168, 205)
    assert (step.prompt, step.output) == (38, 205)
    assert _case("C5_streaming_partials").verified_on_real_stream


# --- the whole suite through real ADK ------------------------------------------------------------


def test_the_reference_plugin_passes_every_case():
    results = run_all(ReferenceAdapter())
    assert [(s.case_id, s.reason) for s in results if s.verdict != "PASS"] == []


def test_the_naive_plugin_does_not_pass_the_cases_it_is_wrong_on():
    by_id = {s.case_id: s for s in run_all(NaiveAdapter())}
    assert (
        by_id["S0_sanity"].verdict == "PASS"
    )  # a plain call is priced correctly: scorecard is valid
    for case_id in (
        "C1_unknown_model",  # guessed
        "C2_cached_tokens",  # cached billed as fresh input
        "C3_thinking_tokens",  # thinking dropped
        "C4_double_registration",  # counted twice
        "C5_streaming_partials",  # every partial priced
        "G1_grounding_gemini_2_5",
        "G2_grounding_gemini_3",
        "G3_grounding_via_agent_tool",
        "G1r_grounding_gemini_2_5_real_shape",
        "G2r_grounding_gemini_3_real_shape",
        "G3r_grounding_via_agent_tool_real_shape",
        "T1_tool_use_prompt_tokens",
        "A1_audio_input",
    ):
        assert by_id[case_id].verdict != "PASS", case_id
    assert by_id["C4_double_registration"].verdict == "FAIL"
    assert "2.00x" in by_id["C4_double_registration"].reason
