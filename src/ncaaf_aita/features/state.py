from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import math
import pandas as pd


@dataclass
class TeamState:
    team: str
    offense_ppd: float = 2.55
    defense_ppd_allowed: float = 2.55
    possessions_mean: float = 12.2
    possessions_sd: float = 1.35
    td_share: float = 0.70
    fg_share: float = 0.30
    turnover_rate: float = 0.12
    explosive_rate: float = 0.12
    explosive_rate_allowed: float = 0.12
    pass_rate: float = 0.50
    first_half_possessions: float = 6.1
    turnover_creation_rate: float = 0.12
    red_zone_td_rate: float = 0.60
    def_red_zone_td_rate_allowed: float = 0.60
    sack_rate_allowed: float = 0.06
    sack_rate_created: float = 0.06
    third_down_success: float = 0.40
    fourth_down_success: float = 0.52
    pass_epa_per_play: float = 0.0
    rush_epa_per_play: float = 0.0
    success_rate: float = 0.43
    def_success_rate_allowed: float = 0.43
    points_per_drive: float = 2.55
    points_per_drive_allowed: float = 2.55
    scoring_opportunity_rate: float = 0.35
    fg_make_rate: float = 0.75
    qb_continuity: float = 0.50
    roster_continuity: float = 0.50
    special_teams_rating: float = 0.0
    offense_sigma: float = 0.16
    defense_sigma: float = 0.16
    sample_size: int = 0
    source_quality: float = 0.70
    fcs_data_sparse: bool = False
    roster_known: bool = False
    qb_known: bool = False
    pbp_known: bool = False
    starter_qb_id: str | None = None
    core_overall: float | None = None
    core_offense: float | None = None
    core_defense: float | None = None
    sp_rating: float | None = None
    elo_rating: float | None = None
    opponent_adjustment_source: str | None = None

    @classmethod
    def from_row(cls, row: pd.Series | dict[str, Any]):
        d = dict(row)
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: d[k] for k in allowed if k in d and not pd.isna(d[k])})

    def to_dict(self):
        return asdict(self)


@dataclass
class WeatherState:
    temperature_f: float | None = None
    wind_speed_mph: float | None = None
    wind_gust_mph: float | None = None
    precip_probability: float | None = None
    precip_amount: float | None = None
    humidity: float | None = None
    weather_code: int | None = None


def weather_scoring_multiplier(w: WeatherState | None, pass_rate: float) -> float:
    if w is None:
        return 1.0
    wind = max(0.0, float(w.wind_speed_mph or 0.0))
    gust = max(0.0, float(w.wind_gust_mph or 0.0))
    # Nonlinear wind penalty; stronger for pass-heavy offenses. Rain is deliberately not a hardcoded under switch.
    effective = max(wind, 0.65 * gust)
    penalty = 0.0
    if effective > 12:
        penalty += ((effective - 12) / 30.0) ** 1.35 * (0.55 + pass_rate)
    temp = w.temperature_f
    if temp is not None and temp < 25:
        penalty += min(0.05, (25 - temp) * 0.0015)
    return max(0.78, 1.0 - penalty)
