from types import SimpleNamespace

import numpy as np
import pandas as pd

from ncaaf_aita.data.odds import OddsApiAdapter
from ncaaf_aita.ev.engine import price_candidate
from ncaaf_aita.pipeline import _best_market_offer, _distribution_for


def test_team_total_normalization_assigns_explicit_home_away_role():
    payload = [{
        "id": "E1",
        "home_team": "Iowa Hawkeyes",
        "away_team": "Iowa State Cyclones",
        "bookmakers": [{
            "key": "testbook",
            "title": "Test Book",
            "markets": [{
                "key": "team_totals",
                "outcomes": [
                    {"name": "Over", "description": "Iowa Hawkeyes", "point": 20.5, "price": -110},
                    {"name": "Under", "description": "Iowa Hawkeyes", "point": 20.5, "price": -110},
                    {"name": "Over", "description": "Iowa State Cyclones", "point": 13.5, "price": -110},
                    {"name": "Under", "description": "Iowa State Cyclones", "point": 13.5, "price": -110},
                ],
            }],
        }],
    }]
    df = OddsApiAdapter.normalize(payload)
    roles = dict(df[["team_if_applicable", "team_role"]].drop_duplicates().values.tolist())
    assert roles["Iowa Hawkeyes"] == "HOME"
    assert roles["Iowa State Cyclones"] == "AWAY"


def test_iowa_cannot_inherit_iowa_state_team_total_offer():
    market = pd.DataFrame([
        {"odds_event_id":"E1","market_family":"TEAM_TOTAL","period":"FG","team_if_applicable":"Iowa Hawkeyes","team_role":"HOME","side":"OVER","point":20.5,"american_price":-110,"bookmaker":"b","bookmaker_title":"B"},
        {"odds_event_id":"E1","market_family":"TEAM_TOTAL","period":"FG","team_if_applicable":"Iowa Hawkeyes","team_role":"HOME","side":"UNDER","point":20.5,"american_price":-110,"bookmaker":"b","bookmaker_title":"B"},
        {"odds_event_id":"E1","market_family":"TEAM_TOTAL","period":"FG","team_if_applicable":"Iowa State Cyclones","team_role":"AWAY","side":"OVER","point":13.5,"american_price":-110,"bookmaker":"b","bookmaker_title":"B"},
        {"odds_event_id":"E1","market_family":"TEAM_TOTAL","period":"FG","team_if_applicable":"Iowa State Cyclones","team_role":"AWAY","side":"UNDER","point":13.5,"american_price":-110,"bookmaker":"b","bookmaker_title":"B"},
    ])
    home = _best_market_offer(market, "E1", "TEAM_TOTAL", ["Iowa Hawkeyes", "Iowa"], team_role="HOME")
    away = _best_market_offer(market, "E1", "TEAM_TOTAL", ["Iowa State Cyclones", "Iowa State"], team_role="AWAY")
    assert home["point"] == 20.5
    assert home["team_if_applicable"] == "Iowa Hawkeyes"
    assert home["team_role"] == "HOME"
    assert away["point"] == 13.5
    assert away["team_if_applicable"] == "Iowa State Cyclones"
    assert away["team_role"] == "AWAY"


def test_team_total_distribution_uses_explicit_role_not_prefix():
    sim = SimpleNamespace(home_points=np.array([20, 21, 22]), away_points=np.array([10, 11, 12]))
    row = pd.Series({"market_family":"TEAM_TOTAL","team_if_applicable":"Iowa State Cyclones","team_role":"AWAY"})
    vals = _distribution_for(row, sim, home_display="Iowa Hawkeyes", away_display="Iowa State Cyclones", home_model="Iowa", away_model="Iowa State")
    assert np.array_equal(vals, sim.away_points)


def test_conservative_probability_is_never_more_optimistic_than_mc_or_blend():
    m = price_candidate(p_mc=.37, p_market=.39, price=150, model_weight=.5, conservative_strength=.5)
    assert m["EV_RAW"] < 0
    assert m["EV_BLEND"] < 0
    assert m["P_CONSERVATIVE"] <= m["P_MC"] + 1e-12
    assert m["P_CONSERVATIVE"] <= m["P_BLEND"] + 1e-12
    assert m["EV_CONSERVATIVE"] <= min(m["EV_RAW"], m["EV_BLEND"]) + 1e-12
    assert m["EV_CONSERVATIVE"] < 0


def test_no_conservative_positive_sign_flip_grid():
    for p_mc in np.linspace(.20, .75, 12):
        for p_market in np.linspace(.20, .75, 12):
            for price in (-150, -110, 100, 130, 180):
                m = price_candidate(p_mc=p_mc, p_market=p_market, price=price, model_weight=.55, conservative_strength=.6)
                if m["EV_RAW"] < 0 and m["EV_BLEND"] < 0:
                    assert m["EV_CONSERVATIVE"] <= 0
