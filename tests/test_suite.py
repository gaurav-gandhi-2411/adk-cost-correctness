"""The suite must be satisfiable (the reference plugin passes everything) and must discriminate (the
naive plugin fails each case for the reason the case exists). Scoring rules are unit-tested with
synthetic outcomes, including "a close guess still fails"."""

from __future__ import annotations

import pytest

from adk_cost_correctness.adapters.reference import NaiveAdapter, ReferenceAdapter
from adk_cost_correctness.cases import Case, all_cases
from adk_cost_correctness.harness import run_all
from adk_cost_correctness.scoring import Outcome, score


def _case(case_id: str) -> Case:
    return next(c for c in all_cases() if c.id == case_id)


# --- scoring rules, no ADK involved --------------------------------------------------------------


def test_a_close_guess_for_an_unknown_model_fails():
    # The fixture's real answer is "no figure". $0.55 is what a $0.30/$2.50 fallback gives for
    # 1M in / 100k out -- and even a figure within 1% of anything would fail the same way.
    s = score(_case("C1_unknown_model"), Outcome(total_usd=0.55))
    assert not s.passed and "guess" in s.reason


def test_zero_is_also_a_guess_for_an_unknown_model():
    assert not score(_case("C1_unknown_model"), Outcome(total_usd=0.0)).passed


def test_flagging_an_unknown_model_while_still_reporting_a_number_fails():
    assert not score(_case("C1_unknown_model"), Outcome(total_usd=0.55, flagged=True)).passed


def test_no_figure_passes_an_unknown_model_however_it_is_reported():
    assert score(_case("C1_unknown_model"), Outcome(total_usd=None, flagged=True)).passed
    assert score(_case("C1_unknown_model"), Outcome(total_usd=None, refused="ValueError: x")).passed


def test_a_cost_case_needs_the_expected_figure_within_half_a_microdollar():
    case = _case("C2_cached_tokens")  # $0.00109
    assert score(case, Outcome(total_usd=0.00109)).passed
    assert score(case, Outcome(total_usd=0.0010904)).passed  # per-call rounding to 7 decimals
    assert not score(case, Outcome(total_usd=0.00110)).passed


def test_double_registration_passes_by_counting_once_or_by_refusing_and_fails_at_2x():
    case = _case("C4_double_registration")  # one call = $0.0008
    assert score(case, Outcome(total_usd=0.0008)).passed
    assert score(case, Outcome(total_usd=None, refused="DoubleRegistrationError: ...")).passed
    twice = score(case, Outcome(total_usd=0.0016))
    assert not twice.passed and "2.00x" in twice.reason


def test_a_missing_figure_fails_a_cost_case():
    assert not score(_case("S0_sanity"), Outcome(total_usd=None)).passed


# --- the fixtures' own arithmetic ----------------------------------------------------------------


@pytest.mark.parametrize(
    ("case_id", "expected"),
    [
        ("S0_sanity", 0.0008),
        ("C2_cached_tokens", 0.00109),
        ("C3_thinking_tokens", 0.00305),
        ("C4_double_registration", 0.0008),
        ("C5_streaming_partials", 0.0005239),  # 38 in + 205 out, from the real recorded stream
    ],
)
def test_expected_costs_match_the_hand_arithmetic_in_the_case_comments(case_id, expected):
    assert _case(case_id).expected_usd == pytest.approx(expected, abs=1e-9)


def test_the_streaming_fixture_is_the_recorded_real_stream():
    step = _case("C5_streaming_partials").step
    assert step.partial_outputs == (4, 22, 71, 120, 168, 205)
    assert (step.prompt, step.output) == (38, 205)
    assert _case("C5_streaming_partials").verified_on_real_stream


# --- the whole suite through real ADK ------------------------------------------------------------


def test_the_reference_plugin_passes_every_case():
    results = run_all(ReferenceAdapter())
    assert [s.case_id for s in results if not s.passed] == []


def test_the_naive_plugin_fails_each_graded_case_for_its_reason():
    by_id = {s.case_id: s for s in run_all(NaiveAdapter())}
    assert by_id["S0_sanity"].passed  # a plain call is priced correctly: the scorecard is valid
    assert not by_id["C1_unknown_model"].passed
    assert not by_id["C2_cached_tokens"].passed  # cached tokens billed at the full input rate
    assert not by_id["C3_thinking_tokens"].passed  # thinking tokens dropped
    assert not by_id["C4_double_registration"].passed
    assert "2.00x" in by_id["C4_double_registration"].reason
    assert not by_id["C5_streaming_partials"].passed  # every partial priced
