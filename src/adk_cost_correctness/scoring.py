"""The scoring rule, in code. See SCORING.md for the prose version and the reasoning."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .cases import Case

# Half a millionth of a dollar: some tools round each call to 7 decimals, and that is not a defect.
ABS_TOL_USD = 5e-7


@dataclass(frozen=True)
class Outcome:
    """What a tool reported for one case, as normalised by its adapter.

    total_usd     the dollar figure the tool reports for the run; None if it reports no figure
    flagged       the tool said (in its output) that it could not price the call
    refused       an error/exception the tool raised instead of continuing, if any
    """

    total_usd: float | None
    flagged: bool = False
    refused: str | None = None


@dataclass(frozen=True)
class Score:
    case_id: str
    passed: bool
    reason: str
    reported_usd: float | None
    expected_usd: float | None


def score(case: Case, outcome: Outcome) -> Score:
    reported, expected = outcome.total_usd, case.expected_usd

    if case.kind == "unpriced":
        # A figure of ANY size -- including 0.0, or a fallback that lands close -- is a guess.
        if reported is None:
            how = (
                "refused"
                if outcome.refused
                else "flagged unknown"
                if outcome.flagged
                else "no figure"
            )
            return Score(case.id, True, f"reported no price ({how})", None, None)
        return Score(
            case.id,
            False,
            f"priced a model with no published price: reported ${reported:.7f} "
            f"({'flagged' if outcome.flagged else 'not flagged'} as unknown) -- any figure is a guess",
            reported,
            None,
        )

    assert expected is not None
    if (
        case.kind == "cost_or_refusal"
        and outcome.refused is not None
        and reported is not None
        and math.isclose(reported, expected, rel_tol=0.0, abs_tol=ABS_TOL_USD)
    ):
        return Score(
            case.id,
            True,
            f"refused the second registration ({outcome.refused[:60]}...) "
            f"and holds a single-count figure: ${reported:.7f}",
            reported,
            expected,
        )
    if case.kind == "cost_or_refusal" and outcome.refused is not None and reported is None:
        return Score(
            case.id,
            True,
            f"refused before reporting a number: {outcome.refused[:90]}",
            None,
            expected,
        )
    if reported is None:
        why = f"raised: {outcome.refused[:90]}" if outcome.refused else "reported no figure"
        return Score(case.id, False, f"expected ${expected:.7f}; {why}", None, expected)
    if math.isclose(reported, expected, rel_tol=0.0, abs_tol=ABS_TOL_USD):
        return Score(case.id, True, f"${reported:.7f} matches", reported, expected)
    ratio = f"{reported / expected:.2f}x" if expected else "n/a"
    return Score(
        case.id,
        False,
        f"expected ${expected:.7f}, reported ${reported:.7f} ({ratio})",
        reported,
        expected,
    )
