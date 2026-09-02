from __future__ import annotations

from dataclasses import dataclass
from ncaaf_aita.features.state import TeamState


@dataclass
class ConfidenceResult:
    score: float
    band: str
    components: dict[str, float]


def _band(x: float):
    if x >= 90: return "ELITE"
    if x >= 80: return "HIGH"
    if x >= 70: return "TRADABLE"
    if x >= 60: return "WATCH"
    return "PASS"


def score_confidence(home: TeamState, away: TeamState, *, converged: bool, market_pair: bool,
                     weather_available: bool, entity_quality: float = 1.0, early_season: bool = False,
                     model_market_gap_pp: float = 0.0, historical_calibration: float = 0.75) -> ConfidenceResult:
    sample = min(1.0, (home.sample_size + away.sample_size) / 12.0)
    roster = (home.roster_continuity + away.roster_continuity + home.qb_continuity + away.qb_continuity) / 4.0
    source = (home.source_quality + away.source_quality) / 2.0
    comps = {
        "data_quality": source,
        "roster_qb_certainty": roster,
        "sample_size": sample,
        "simulation_convergence": 1.0 if converged else 0.2,
        "market_pair": 1.0 if market_pair else 0.45,
        "model_market_agreement": max(0.25, 1.0 - abs(model_market_gap_pp)/25.0),
        "historical_calibration": max(0.0, min(1.0, historical_calibration)),
        "weather_certainty": 1.0 if weather_available else 0.72,
        "entity_resolution": entity_quality,
    }
    weights = {"data_quality":.17,"roster_qb_certainty":.15,"sample_size":.11,"simulation_convergence":.16,"market_pair":.09,"model_market_agreement":.10,"historical_calibration":.08,"weather_certainty":.06,"entity_resolution":.08}
    score = 100*sum(comps[k]*weights[k] for k in weights)
    if early_season:
        score = min(score, 89.0 if roster >= 0.72 else 82.0)
    if home.fcs_data_sparse or away.fcs_data_sparse:
        score = min(score, 69.0)
    return ConfidenceResult(round(score, 2), _band(score), comps)
