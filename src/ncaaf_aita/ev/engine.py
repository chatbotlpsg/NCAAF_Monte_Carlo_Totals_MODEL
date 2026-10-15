from __future__ import annotations

from ncaaf_aita.pricing.odds_math import american_to_profit_factor, american_to_break_even, probability_to_american


def ev_percent(probability: float, american_odds: float) -> float:
    b = american_to_profit_factor(american_odds)
    p = float(probability)
    return 100.0 * (p*b - (1.0-p))


def ev_percent_with_push(probability_conditional: float, american_odds: float, p_push: float = 0.0) -> float:
    """EV per dollar staked when push returns stake.

    probability_conditional is P(win | non-push), which is the probability comparable to a standard two-way market quote.
    """
    action = max(0.0, min(1.0, 1.0-float(p_push)))
    return action * ev_percent(probability_conditional, american_odds)


def kelly_fraction(probability: float, american_odds: float) -> float:
    b = american_to_profit_factor(american_odds)
    return max(0.0, (b*probability - (1-probability))/b)


def price_candidate(p_mc: float, p_market: float, price: float, model_weight: float, conservative_strength: float, p_push: float = 0.0):
    p_mc = max(0.0, min(1.0, float(p_mc)))
    p_market = max(0.0, min(1.0, float(p_market)))
    w = max(0.0, min(1.0, float(model_weight)))
    strength = max(0.0, min(1.0, float(conservative_strength)))

    p_blend = w*p_mc + (1-w)*p_market

    # One-way lower-bound probability for the selected side.
    # Conservative probability can never be more optimistic than the
    # pure model or blended model and therefore cannot create a +EV
    # sign flip when raw/blended EV are both negative.
    base_lower = min(p_mc, p_blend)
    disagreement = abs(p_mc - p_market)
    haircut = (1.0 - strength) * disagreement
    p_cons = max(0.0, min(base_lower, base_lower - haircut))

    return {
        "P_MC": p_mc,
        "P_MARKET_FAIR": p_market,
        "P_BLEND": p_blend,
        "P_CONSERVATIVE": p_cons,
        "P_BREAK_EVEN": american_to_break_even(price),
        "FAIR_PRICE_MC": probability_to_american(p_mc),
        "FAIR_PRICE_BLEND": probability_to_american(p_blend),
        "FAIR_PRICE_CONSERVATIVE": probability_to_american(p_cons),
        "EV_RAW": ev_percent_with_push(p_mc, price, p_push),
        "EV_BLEND": ev_percent_with_push(p_blend, price, p_push),
        "EV_CONSERVATIVE": ev_percent_with_push(p_cons, price, p_push),
        "KELLY_FULL_CONSERVATIVE": (1.0-p_push) * kelly_fraction(p_cons, price),
    }
