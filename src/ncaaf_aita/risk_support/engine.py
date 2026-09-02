from __future__ import annotations


def quant_grade(ev_cons_pct: float, confidence: float, blocked: bool, cfg) -> str:
    # This is a mechanical candidate grade only. Final PASS/WATCH/VALUE/ELITE belongs to the external Trading Agent.
    if blocked: return "PASS"
    if ev_cons_pct < 0: return "ENTERTAINMENT"
    if ev_cons_pct >= 100*cfg.get("risk.quant_elite_min_ev", .06) and confidence >= cfg.get("risk.elite_min_confidence", 82):
        return "ELITE_CANDIDATE"
    if ev_cons_pct >= 100*cfg.get("risk.quant_value_min_ev", .025) and confidence >= cfg.get("risk.value_min_confidence", 72):
        return "VALUE_CANDIDATE"
    if ev_cons_pct >= 100*cfg.get("risk.quant_watch_min_ev", .005): return "WATCH"
    return "PASS"


def stake_support(kelly_full: float, cfg) -> dict:
    frac = cfg.get("risk.default_fractional_kelly", .25)
    kelly_input = min(kelly_full*frac, cfg.get("risk.max_fractional_kelly_input", .50))
    if kelly_input >= .01: tier = "A"
    elif kelly_input >= .005: tier = "B"
    elif kelly_input > 0: tier = "C"
    else: tier = "NONE"
    return {"recommended_fractional_kelly_input": kelly_input, "max_stake_tier": tier}
