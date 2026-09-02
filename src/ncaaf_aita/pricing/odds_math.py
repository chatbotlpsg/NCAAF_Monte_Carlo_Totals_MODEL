from __future__ import annotations


def american_to_break_even(odds: float) -> float:
    odds = float(odds)
    if odds < 0:
        a = abs(odds); return a / (a + 100.0)
    return 100.0 / (odds + 100.0)


def american_to_profit_factor(odds: float) -> float:
    odds = float(odds)
    return 100.0 / abs(odds) if odds < 0 else odds / 100.0


def probability_to_american(p: float) -> float:
    p = min(max(float(p), 1e-9), 1-1e-9)
    if p >= 0.5:
        return -100.0 * p / (1.0 - p)
    return 100.0 * (1.0 - p) / p


def vig_free_two_way(over_odds: float, under_odds: float) -> tuple[float, float, float]:
    po = american_to_break_even(over_odds)
    pu = american_to_break_even(under_odds)
    s = po + pu
    return po/s, pu/s, s - 1.0
