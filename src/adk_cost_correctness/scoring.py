"""The scoring rule, in code. See docs/SCORING.md for the prose version and the reasoning.

Three outcomes per case:

  PASS        the correct figure; or "no figure" when no vendor publishes a price
  INCOMPLETE  "no figure", or a figure that leaves out a component whose price the vendor DOES publish
              (an undercount that is missing something, not something wrong)
  FAIL        any other figure, including ANY figure for a genuinely unpriceable component; a run that
              crashed instead of answering (except where refusing is the correct answer)
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from .cases import Case

# Half a millionth of a dollar: some tools round each call to 7 decimals, and that is not a defect.
ABS_TOL_USD = 5e-7

Verdict = Literal["PASS", "INCOMPLETE", "FAIL"]


@dataclass(frozen=True)
class Outcome:
    """What a tool reported for one case, as normalised by its adapter.

    total_usd     the dollar figure the tool reports for the run; None if it reports no figure
    flagged       the tool said (in its output) that it could not price something
    refused       an error/exception the tool raised instead of continuing, if any
    """

    total_usd: float | None
    flagged: bool = False
    refused: str | None = None


@dataclass(frozen=True)
class Score:
    case_id: str
    verdict: Verdict
    reason: str
    reported_usd: float | None
    expected_usd: float | None

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=ABS_TOL_USD)


def _score_unpriced(case: Case, outcome: Outcome) -> Score:
    # A figure of ANY size -- including 0.0, or a fallback that lands close -- is a guess.
    if outcome.total_usd is None:
        how = (
            "refused" if outcome.refused else "flagged unknown" if outcome.flagged else "no figure"
        )
        return Score(case.id, "PASS", f"reported no price ({how})", None, None)
    flag = "flagged" if outcome.flagged else "not flagged"
    return Score(
        case.id,
        "FAIL",
        f"priced a model with no published price: reported ${outcome.total_usd:.7f} "
        f"({flag} as unknown) -- any figure is a guess",
        outcome.total_usd,
        None,
    )


def score(case: Case, outcome: Outcome) -> Score:
    if case.kind == "unpriced":
        return _score_unpriced(case, outcome)

    reported, expected = outcome.total_usd, case.expected_usd
    assert expected is not None
    if case.kind == "cost_or_refusal" and outcome.refused is not None:
        if reported is None:
            return Score(
                case.id,
                "PASS",
                f"refused before reporting a number: {outcome.refused[:90]}",
                None,
                expected,
            )
        if _close(reported, expected):
            return Score(
                case.id,
                "PASS",
                f"refused the second registration ({outcome.refused[:60]}...) "
                f"and holds a single-count figure: ${reported:.7f}",
                reported,
                expected,
            )
    if outcome.refused is not None and reported is None:
        return Score(
            case.id, "FAIL", f"raised instead of answering: {outcome.refused[:90]}", None, expected
        )
    if reported is None:
        how = "flagged it unknown" if outcome.flagged else "reported no figure"
        return Score(
            case.id,
            "INCOMPLETE",
            f"a price is published (${expected:.7f}) but the tool {how}",
            None,
            expected,
        )
    if _close(reported, expected):
        return Score(case.id, "PASS", f"${reported:.7f} matches", reported, expected)
    if any(_close(reported, alt) for alt in case.also_pass_usd):
        return Score(
            case.id,
            "PASS",
            f"${reported:.7f} matches an accepted alternative (expected ${expected:.7f}; "
            "the case's billing of one component is not established)",
            reported,
            expected,
        )
    if any(_close(reported, partial) for partial in case.incomplete_usd):
        silent = "" if outcome.flagged else ", not flagged as incomplete"
        return Score(
            case.id,
            "INCOMPLETE",
            f"${reported:.7f} leaves out a component with a published price "
            f"(expected ${expected:.7f}, {reported / expected:.2f}x{silent})",
            reported,
            expected,
        )
    ratio = f"{reported / expected:.2f}x" if expected else "n/a"
    return Score(
        case.id,
        "FAIL",
        f"expected ${expected:.7f}, reported ${reported:.7f} ({ratio})",
        reported,
        expected,
    )
