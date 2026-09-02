from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

import numpy as np
import pandas as pd

from ncaaf_aita.common import utc_now_iso, write_json, stable_int_hash
from ncaaf_aita.config import Config
from ncaaf_aita.data.entities import EntityResolver, norm_team
from ncaaf_aita.features.state import TeamState, WeatherState
from ncaaf_aita.simulation.engine import MonteCarloEngine, GameSimulationResult
from ncaaf_aita.pricing.curves import prob_at_line, curve
from ncaaf_aita.pricing.odds_math import vig_free_two_way, probability_to_american
from ncaaf_aita.ev.engine import price_candidate
from ncaaf_aita.confidence.engine import score_confidence
from ncaaf_aita.correlation.engine import indicator_correlation
from ncaaf_aita.risk_support.engine import quant_grade, stake_support
from ncaaf_aita.reporting.boards import render_markdown
from ncaaf_aita.handoff.builder import build_zip


EV_BOARD_COLUMNS = [
    "quant_rank", "aita_event_id", "odds_event_id", "matchup", "market_family", "period",
    "team_if_applicable", "side", "point", "american_price", "bookmaker", "bookmaker_title",
    "P_MC", "P_MARKET_FAIR", "P_BLEND", "P_CONSERVATIVE", "P_BREAK_EVEN", "p_push",
    "FAIR_PRICE_MC", "FAIR_PRICE_BLEND", "FAIR_PRICE_CONSERVATIVE", "EV_RAW", "EV_BLEND",
    "EV_CONSERVATIVE", "confidence", "confidence_band", "quant_grade", "grade_status",
    "calibration_status", "ev_estimate_status", "ev_actionability", "model_weight",
    "blocking_flag", "odds_stale", "KELLY_FULL_CONSERVATIVE", "recommended_fractional_kelly_input",
    "max_stake_tier", "stake_status",
]

FULL_BOARD_COLUMNS = [
    "model_rank", "aita_event_id", "odds_event_id", "matchup", "away_team", "home_team",
    "away_team_model", "home_team_model", "model_mean_total", "model_median_total", "model_fair_total",
    "book_total", "model_total_edge_points", "p_over_book", "p_under_book", "p_push_book",
    "model_lean", "model_over_fair_american", "model_under_fair_american", "best_over_price",
    "best_over_book", "best_under_price", "best_under_book", "market_status", "model_status",
    "home_state_source", "away_state_source", "home_entity_resolution", "away_entity_resolution",
    "simulation_converged", "data_quality_flags",
]

TEAM_BOARD_COLUMNS = [
    "model_rank", "aita_event_id", "odds_event_id", "matchup", "team", "team_model", "home_away",
    "model_mean_points", "model_median_points", "model_fair_team_total", "book_team_total",
    "model_team_total_edge_points", "p_over_book", "p_under_book", "p_push_book", "model_lean",
    "model_over_fair_american", "model_under_fair_american", "best_over_price", "best_over_book",
    "best_under_price", "best_under_book", "market_status", "model_status", "state_source",
    "entity_resolution", "simulation_converged", "data_quality_flags",
]

H1_BOARD_COLUMNS = [
    "model_rank", "aita_event_id", "odds_event_id", "matchup", "away_team", "home_team",
    "model_mean_h1_total", "model_median_h1_total", "model_fair_h1_total", "book_h1_total",
    "model_h1_edge_points", "p_over_book", "p_under_book", "p_push_book", "model_lean",
    "model_over_fair_american", "model_under_fair_american", "best_over_price", "best_over_book",
    "best_under_price", "best_under_book", "market_status", "model_status", "simulation_converged",
    "data_quality_flags",
]


def _with_schema(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        if c not in out.columns:
            out[c] = pd.Series(dtype="object")
    return out[cols + [c for c in out.columns if c not in cols]]


def _model_weight(cfg: Config, early: bool, conf: float):
    if conf < 65:
        return cfg.get("blend.low_confidence_model_weight", .45)
    return cfg.get("blend.early_season_model_weight", .55) if early else cfg.get("blend.mature_model_weight", .72)


def _conservative_strength(conf: float, cfg: Config):
    floor = cfg.get("blend.conservative_shrink_floor", .35)
    return floor + (1-floor)*max(0.0, min(1.0, (conf-50)/50))


def _pair_market_fair(market: pd.DataFrame) -> pd.DataFrame:
    if market.empty:
        return pd.DataFrame(columns=list(market.columns) + ["P_MARKET_FAIR", "vig"])
    keys = ["odds_event_id", "market_family", "period", "team_if_applicable", "point", "bookmaker", "bookmaker_title"]
    rows = []
    for _, g in market.groupby(keys, dropna=False):
        over = g[g.side == "OVER"]
        under = g[g.side == "UNDER"]
        if over.empty or under.empty:
            continue
        ro, ru = over.iloc[0], under.iloc[0]
        try:
            po, pu, vig = vig_free_two_way(float(ro.american_price), float(ru.american_price))
        except Exception:
            continue
        for r, p in ((ro, po), (ru, pu)):
            d = r.to_dict()
            d["P_MARKET_FAIR"] = p
            d["vig"] = vig
            rows.append(d)
    return pd.DataFrame(rows)


def _distribution_for(row, sim: GameSimulationResult, *, home_display: str, away_display: str,
                      home_model: str, away_model: str):
    fam = row["market_family"]
    if fam == "FG_TOTAL":
        return sim.total
    if fam == "H1_TOTAL":
        return sim.h1_total
    if fam == "TEAM_TOTAL":
        team = norm_team(str(row.get("team_if_applicable") or ""))
        home_names = {norm_team(home_display), norm_team(home_model)}
        away_names = {norm_team(away_display), norm_team(away_model)}
        if team in home_names or any(team.startswith(x + " ") for x in home_names if x):
            return sim.home_points
        if team in away_names or any(team.startswith(x + " ") for x in away_names if x):
            return sim.away_points
    return None


def _fallback_state(team_key: str, state_map: dict[str, TeamState]) -> TeamState:
    """Create a dynamic sparse-team prior from the current FBS state universe.

    This is intentionally conservative: a missing/FCS team is centered toward the
    lower offense / weaker defense portion of the known-team distribution and given
    substantially wider latent uncertainty. It enables model coverage without
    pretending the sparse team has the same information quality as an established
    CFBD state.
    """
    states = list(state_map.values())
    if not states:
        return TeamState(
            team=team_key, offense_ppd=2.15, defense_ppd_allowed=2.85, possessions_mean=12.0,
            possessions_sd=1.75, offense_sigma=.50, defense_sigma=.50, source_quality=.20,
            sample_size=0, fcs_data_sparse=True, roster_known=False, qb_known=False,
            pbp_known=False, qb_continuity=.30, roster_continuity=.35,
            state_source="DYNAMIC_SPARSE_PRIOR_EMPTY_UNIVERSE", fallback_state=True,
        )

    def vals(attr):
        return np.asarray([float(getattr(s, attr)) for s in states if np.isfinite(float(getattr(s, attr)))], dtype=float)

    off = vals("offense_ppd")
    deff = vals("defense_ppd_allowed")
    poss = vals("possessions_mean")
    poss_sd = vals("possessions_sd")
    td = vals("td_share")
    fg = vals("fg_share")
    to = vals("turnover_rate")
    exp = vals("explosive_rate")
    pas = vals("pass_rate")
    sig_o = vals("offense_sigma")
    sig_d = vals("defense_sigma")

    return TeamState(
        team=team_key,
        offense_ppd=float(np.quantile(off, .25)) if off.size else 2.15,
        defense_ppd_allowed=float(np.quantile(deff, .75)) if deff.size else 2.85,
        possessions_mean=float(np.median(poss)) if poss.size else 12.0,
        possessions_sd=max(1.65, float(np.quantile(poss_sd, .75)) if poss_sd.size else 1.65),
        td_share=float(np.median(td)) if td.size else .68,
        fg_share=float(np.median(fg)) if fg.size else .25,
        turnover_rate=min(.20, max(.12, float(np.quantile(to, .65)) if to.size else .14)),
        turnover_creation_rate=.11,
        explosive_rate=float(np.quantile(exp, .30)) if exp.size else .10,
        explosive_rate_allowed=.14,
        pass_rate=float(np.median(pas)) if pas.size else .50,
        first_half_possessions=(float(np.median(poss)) if poss.size else 12.0) / 2.0,
        qb_continuity=.30,
        roster_continuity=.35,
        offense_sigma=max(.42, float(np.quantile(sig_o, .90)) if sig_o.size else .42),
        defense_sigma=max(.42, float(np.quantile(sig_d, .90)) if sig_d.size else .42),
        sample_size=0,
        source_quality=.28,
        fcs_data_sparse=True,
        roster_known=False,
        qb_known=False,
        pbp_known=False,
        opponent_adjustment_source="DYNAMIC_SPARSE_PRIOR",
        state_source="DYNAMIC_SPARSE_PRIOR",
        fallback_state=True,
    )


def _resolve_state(ev: pd.Series, side: str, state_map: dict[str, TeamState], resolver: EntityResolver):
    display = str(ev.get(f"{side}_team") or "")
    model_hint = str(ev.get(f"{side}_team_model") or "")
    candidates = list(state_map)

    for name, method in ((model_hint, "ESPN_LOCATION_EXACT"), (display, "DISPLAY_EXACT")):
        if name and name in state_map:
            return state_map[name], name, method, False

    # ESPN location/model hints are school names, not mascot display names. Do not
    # shorten an unresolved location to a larger FBS program (e.g. Arkansas-Pine
    # Bluff -> Arkansas). Exact/fuzzy only for the model hint. Mascot-prefix logic
    # is reserved for the human display name when no model hint is available.
    if model_hint and model_hint.lower() != "nan":
        resolved, method = resolver.resolve_team(model_hint, candidates, allow_mascot_prefix=False)
        if resolved is not None:
            return state_map[resolved], resolved, method, False
    else:
        resolved, method = resolver.resolve_team(display, candidates, allow_mascot_prefix=True)
        if resolved is not None:
            return state_map[resolved], resolved, method, False

    fallback_key = model_hint if model_hint and model_hint.lower() != "nan" else display
    return _fallback_state(fallback_key, state_map), fallback_key, "FALLBACK_DYNAMIC_SPARSE_PRIOR", True


def _fair_line_from_curve(c: pd.DataFrame) -> tuple[float, float, float, float]:
    if c.empty:
        return float("nan"), float("nan"), float("nan"), float("nan")
    x = c.copy()
    x["balance"] = (x["p_over"] - x["p_under"]).abs()
    r = x.sort_values(["balance", "line"]).iloc[0]
    return float(r.line), float(r.p_over), float(r.p_under), float(r.p_push)


def _best_market_offer(market: pd.DataFrame, odds_event_id: str, family: str, team_names: list[str] | None = None):
    if market.empty or not odds_event_id or odds_event_id == "nan":
        return None
    g = market[(market["odds_event_id"].astype(str) == str(odds_event_id)) & (market["market_family"] == family)].copy()
    if g.empty:
        return None
    if family == "TEAM_TOTAL":
        valid = {norm_team(x) for x in (team_names or []) if x}
        g = g[g["team_if_applicable"].astype(str).map(norm_team).map(
            lambda n: n in valid or any(n.startswith(v + " ") or v.startswith(n + " ") for v in valid if v and n)
        )]
        if g.empty:
            return None
    g["point"] = pd.to_numeric(g["point"], errors="coerce")
    g["american_price"] = pd.to_numeric(g["american_price"], errors="coerce")
    g = g.dropna(subset=["point", "american_price"])
    if g.empty:
        return None
    points = g["point"].value_counts()
    max_count = points.max()
    candidate_points = sorted(points[points == max_count].index.astype(float))
    target = float(np.median(candidate_points))
    point = min(candidate_points, key=lambda x: abs(x-target))
    gp = g[g["point"] == point]
    over = gp[gp.side == "OVER"].sort_values("american_price", ascending=False)
    under = gp[gp.side == "UNDER"].sort_values("american_price", ascending=False)
    if over.empty or under.empty:
        return None
    ro, ru = over.iloc[0], under.iloc[0]
    return {
        "point": point,
        "best_over_price": float(ro.american_price), "best_over_book": ro.get("bookmaker_title") or ro.get("bookmaker"),
        "best_under_price": float(ru.american_price), "best_under_book": ru.get("bookmaker_title") or ru.get("bookmaker"),
    }


def _lean_at_line(values: np.ndarray, line: float):
    po, push = prob_at_line(values, line, "OVER")
    pu, _ = prob_at_line(values, line, "UNDER")
    action = max(1e-12, 1.0-push)
    poc, puc = po/action, pu/action
    if abs(poc-puc) < .01:
        lean = "NEUTRAL"
    else:
        lean = "OVER" if poc > puc else "UNDER"
    return po, pu, push, poc, puc, lean


def model_first_shortlist(*, cfg: Config, slate: pd.DataFrame, team_states: pd.DataFrame,
                          full_totals_market: pd.DataFrame, max_events: int | None = None,
                          simulation_count: int | None = None, weather_by_event: dict | None = None) -> pd.DataFrame:
    """Pure-football prescreen before derivative market calls.

    Missing team states are assigned a high-uncertainty sparse prior instead of
    removing the game. Missing Odds API event IDs still prevent a derivative API
    call, but do not prevent model pricing in the final pipeline.
    """
    state_map = {str(r["team"]): TeamState.from_row(r) for _, r in team_states.iterrows()}
    resolver = EntityResolver()
    weather_by_event = weather_by_event or {}
    k = int(max_events or cfg.get("odds.max_derivative_events_per_run", 12))
    n = int(simulation_count or min(50000, cfg.get("simulation.production_count", 100000)))
    lines = full_totals_market[full_totals_market["market_family"] == "FG_TOTAL"].copy() if not full_totals_market.empty else pd.DataFrame()
    rows=[]
    for _, ev in slate.iterrows():
        eid=str(ev.get("aita_event_id") or ev.get("odds_event_id") or ev.get("espn_event_id"))
        oid=str(ev.get("odds_event_id") or "")
        if not oid or oid == "nan":
            continue
        home_display, away_display = str(ev.get("home_team")), str(ev.get("away_team"))
        h, home_model, hmeth, hfallback = _resolve_state(ev, "home", state_map, resolver)
        a, away_model, ameth, afallback = _resolve_state(ev, "away", state_map, resolver)
        wraw = weather_by_event.get(eid)
        weather = WeatherState(**wraw) if isinstance(wraw, dict) else None
        sim=MonteCarloEngine(seed=int(cfg.get("simulation.seed",20260901)) + stable_int_hash(eid)).simulate(
            h, a, n, weather, bool(ev.get("neutral_site",False)))
        g=lines[lines.odds_event_id.astype(str)==oid] if not lines.empty else pd.DataFrame()
        market_line=float(pd.to_numeric(g.get("point"), errors="coerce").dropna().median()) if not g.empty else float("nan")
        mean_total=float(np.mean(sim.total)); h1=float(np.mean(sim.h1_total)); home_pts=float(np.mean(sim.home_points)); away_pts=float(np.mean(sim.away_points))
        disagreement=abs(mean_total-market_line) if np.isfinite(market_line) else 0.0
        asymmetry=abs(home_pts-away_pts)
        h1_structure=abs(h1 - 0.5*mean_total)
        uncertainty=(h.offense_sigma+h.defense_sigma+a.offense_sigma+a.defense_sigma)/4
        continuity=(h.qb_continuity+a.qb_continuity+h.roster_continuity+a.roster_continuity)/4
        source_quality=(h.source_quality+a.source_quality)/2
        score=(1.25*disagreement + .18*asymmetry + 1.5*h1_structure) * (0.65+0.35*continuity) * max(.25,1.0-uncertainty) * max(.30, source_quality)
        rows.append({
            "aita_event_id":eid,"odds_event_id":oid,"matchup":f"{away_display} @ {home_display}",
            "home_team_model":home_model,"away_team_model":away_model,"home_resolution":hmeth,"away_resolution":ameth,
            "fallback_state_used":bool(hfallback or afallback),"model_mean_total":mean_total,"market_total":market_line,
            "model_market_abs_gap":disagreement,"team_scoring_asymmetry":asymmetry,"h1_structural_difference":h1_structure,
            "uncertainty":uncertainty,"continuity":continuity,"source_quality":source_quality,"derivative_interest_score":score,
        })
    out=pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["derivative_interest_score","model_market_abs_gap"],ascending=False).head(k).reset_index(drop=True)


def run_quant_pipeline(*, cfg: Config, slate: pd.DataFrame, team_states: pd.DataFrame, market: pd.DataFrame,
                       season: int, week: int, slate_date: str, output_root: str | Path = "outputs/handoffs",
                       simulation_count: int | None = None, weather_by_event: dict | None = None,
                       usage_ledger_path: str | Path | None = None) -> Path:
    run_id = f"NCAAF_{season}_W{week:02d}_{uuid4().hex[:10]}"
    os.environ["AITA_RUN_ID"] = run_id
    run_dir = Path(output_root)/run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    early = week <= 3
    n = int(simulation_count or cfg.get("simulation.final_board_count", 250000))
    state_map = {str(r["team"]): TeamState.from_row(r) for _, r in team_states.iterrows()}
    resolver = EntityResolver()
    weather_by_event = weather_by_event or {}
    market = _pair_market_fair(market.copy())
    calibration_status = str(cfg.get("calibration.status", "UNCALIBRATED")).upper()
    ev_estimate_status = "CALIBRATED" if calibration_status == "CALIBRATED" else "PROVISIONAL_UNCALIBRATED"
    historical_calibration_prior = float(cfg.get("calibration.historical_calibration_prior", .50))
    allow_stakes = bool(cfg.get("calibration.allow_python_stake_recommendations", False)) and calibration_status == "CALIBRATED"

    projections=[]; dist_rows=[]; fair_curves=[]; priced=[]; conf_rows=[]; driver_rows=[]; dq=[]; convergence=[]; indicators={}
    full_board=[]; team_board=[]; h1_board=[]; sim_store={}; ctx_store={}

    for event_index, (_, ev) in enumerate(slate.iterrows(), start=1):
        eid = str(ev.get("aita_event_id") or ev.get("odds_event_id") or ev.get("espn_event_id"))
        oid = str(ev.get("odds_event_id") or "")
        home_display, away_display = str(ev.get("home_team") or ""), str(ev.get("away_team") or "")
        h, home_model, hmeth, hfallback = _resolve_state(ev, "home", state_map, resolver)
        a, away_model, ameth, afallback = _resolve_state(ev, "away", state_map, resolver)
        flags=[]
        if hfallback: flags.append(("FALLBACK_TEAM_STATE_HOME","WARN"))
        if afallback: flags.append(("FALLBACK_TEAM_STATE_AWAY","WARN"))
        if not h.roster_known or not a.roster_known: flags.append(("MISSING_ROSTER","WARN"))
        if not h.qb_known or not a.qb_known: flags.append(("MISSING_QB","WARN"))
        if not h.pbp_known or not a.pbp_known: flags.append(("MISSING_PBP","WARN"))
        if h.sample_size < 2 or a.sample_size < 2: flags.append(("LOW_SAMPLE","WARN"))
        if h.fcs_data_sparse or a.fcs_data_sparse: flags.append(("FCS_DATA_SPARSE","WARN"))
        if eid not in weather_by_event: flags.append(("WEATHER_UNAVAILABLE","WARN"))
        if not oid or oid == "nan": flags.append(("MARKET_EVENT_UNMAPPED","WARN"))

        wraw = weather_by_event.get(eid)
        weather = WeatherState(**wraw) if isinstance(wraw, dict) else None
        try:
            engine = MonteCarloEngine(seed=int(cfg.get("simulation.seed",20260901)) + stable_int_hash(eid))
            sim = engine.simulate(h,a,n,weather,bool(ev.get("neutral_site",False)))
        except Exception as exc:
            dq.append({"aita_event_id":eid,"matchup":f"{away_display} @ {home_display}","flags":flags+[(f"SIMULATION_ERROR:{type(exc).__name__}","BLOCK")],"status":"BLOCK"})
            continue

        sim_store[eid]=sim
        ctx_store[eid]={
            "home":h,"away":a,"home_model":home_model,"away_model":away_model,
            "home_display":home_display,"away_display":away_display,
            "home_resolution":hmeth,"away_resolution":ameth,
            "fallback":bool(hfallback or afallback),
        }

        central = round(float(np.median(sim.total))*2)/2
        if n >= 500000: sample_a, sample_b = 250000, 500000
        elif n >= 250000: sample_a, sample_b = 100000, 250000
        else: sample_b, sample_a = n, max(1000, n//2)
        p_a = float(np.mean(sim.total[:sample_a] > central)); p_b=float(np.mean(sim.total[:sample_b] > central))
        delta=abs(p_a-p_b); conv = delta <= cfg.get("simulation.convergence_tolerance",.0075)
        convergence.append({"aita_event_id":eid,"line":central,"sample_a":sample_a,"sample_b":sample_b,"p_sample_a":p_a,"p_sample_b":p_b,"abs_delta":delta,"tolerance":cfg.get("simulation.convergence_tolerance",.0075),"converged":conv})
        if not conv: flags.append(("SIMULATION_NOT_CONVERGED","WARN"))

        model_status = "SPARSE_PRIOR_MODEL" if (hfallback or afallback) else "FULL_MODEL"
        flag_text = "|".join(f"{f}:{s}" for f,s in flags) if flags else "NONE"
        projections.append({
            "aita_event_id":eid,"odds_event_id":oid if oid != "nan" else "","matchup":f"{away_display} @ {home_display}",
            "home_team":home_display,"away_team":away_display,"home_team_model":home_model,"away_team_model":away_model,
            "home_entity_resolution":hmeth,"away_entity_resolution":ameth,"home_state_source":h.state_source or h.opponent_adjustment_source or "CFBD_STATE",
            "away_state_source":a.state_source or a.opponent_adjustment_source or "CFBD_STATE","model_status":model_status,
            "mean_home_points":float(np.mean(sim.home_points)),"median_home_points":float(np.median(sim.home_points)),
            "mean_away_points":float(np.mean(sim.away_points)),"median_away_points":float(np.median(sim.away_points)),
            "mean_total":float(np.mean(sim.total)),"median_total":float(np.median(sim.total)),
            "mean_margin":float(np.mean(sim.home_points-sim.away_points)),"first_half_mean_total":float(np.mean(sim.h1_total)),
            "first_half_median_total":float(np.median(sim.h1_total)),"p10_total":float(np.quantile(sim.total,.10)),"p25_total":float(np.quantile(sim.total,.25)),
            "p75_total":float(np.quantile(sim.total,.75)),"p90_total":float(np.quantile(sim.total,.90)),
            "mean_possessions_home":float(np.mean(sim.home_possessions)),"mean_possessions_away":float(np.mean(sim.away_possessions)),
            "median_margin":float(np.median(sim.home_points-sim.away_points)),
            "p_home_win":float(np.mean(sim.home_points>sim.away_points)),"p_away_win":float(np.mean(sim.away_points>sim.home_points)),"p_tie":float(np.mean(sim.home_points==sim.away_points)),
            "simulation_converged":conv,"data_quality_flags":flag_text,
        })

        fg_lines=np.arange(float(cfg.get("simulation.total_curve_min",30.5)),float(cfg.get("simulation.total_curve_max",90.5))+1e-9,float(cfg.get("simulation.total_curve_step",1.0)))
        tt_lines=np.arange(float(cfg.get("simulation.team_total_min",7.5)),float(cfg.get("simulation.team_total_max",60.5))+1e-9,float(cfg.get("simulation.team_total_step",1.0)))
        h1_lines=np.arange(float(cfg.get("simulation.h1_total_min",14.5)),float(cfg.get("simulation.h1_total_max",48.5))+1e-9,float(cfg.get("simulation.h1_total_step",1.0)))
        curve_map={}
        for fam,label,vals,team_name,lineset in (
            ("FG_TOTAL","full_game_total",sim.total,None,fg_lines),
            ("TEAM_TOTAL","home_team_total",sim.home_points,home_display,tt_lines),
            ("TEAM_TOTAL","away_team_total",sim.away_points,away_display,tt_lines),
            ("H1_TOTAL","first_half_total",sim.h1_total,None,h1_lines),
        ):
            c=curve(vals,lineset,label)
            c.insert(0,"aita_event_id",eid); c.insert(1,"market_family",fam); c.insert(2,"team_if_applicable",team_name)
            fair_curves.extend(c.to_dict("records")); curve_map[label]=c

        for q in (.05,.10,.25,.50,.75,.90,.95):
            dist_rows.append({"aita_event_id":eid,"quantile":q,"home_points":float(np.quantile(sim.home_points,q)),"away_points":float(np.quantile(sim.away_points,q)),"total":float(np.quantile(sim.total,q)),"h1_total":float(np.quantile(sim.h1_total,q))})

        # Full-game model board: one row for every simulated event regardless of market coverage.
        fg_fair, _, _, _ = _fair_line_from_curve(curve_map["full_game_total"])
        offer = _best_market_offer(market, oid, "FG_TOTAL")
        fg_row={
            "model_rank":event_index,"aita_event_id":eid,"odds_event_id":oid if oid != "nan" else "",
            "matchup":f"{away_display} @ {home_display}","away_team":away_display,"home_team":home_display,
            "away_team_model":away_model,"home_team_model":home_model,"model_mean_total":float(np.mean(sim.total)),
            "model_median_total":float(np.median(sim.total)),"model_fair_total":fg_fair,"book_total":np.nan,
            "model_total_edge_points":np.nan,"p_over_book":np.nan,"p_under_book":np.nan,"p_push_book":np.nan,
            "model_lean":"MODEL_ONLY","model_over_fair_american":np.nan,"model_under_fair_american":np.nan,
            "best_over_price":np.nan,"best_over_book":"","best_under_price":np.nan,"best_under_book":"",
            "market_status":"MODEL_ONLY_NO_EXACT_MARKET","model_status":model_status,
            "home_state_source":h.state_source or h.opponent_adjustment_source or "CFBD_STATE",
            "away_state_source":a.state_source or a.opponent_adjustment_source or "CFBD_STATE",
            "home_entity_resolution":hmeth,"away_entity_resolution":ameth,"simulation_converged":conv,"data_quality_flags":flag_text,
        }
        if offer:
            po, pu, pp, poc, puc, lean = _lean_at_line(sim.total, offer["point"])
            fg_row.update({
                "book_total":offer["point"],"model_total_edge_points":fg_fair-offer["point"],
                "p_over_book":po,"p_under_book":pu,"p_push_book":pp,"model_lean":lean,
                "model_over_fair_american":probability_to_american(poc),"model_under_fair_american":probability_to_american(puc),
                "best_over_price":offer["best_over_price"],"best_over_book":offer["best_over_book"],
                "best_under_price":offer["best_under_price"],"best_under_book":offer["best_under_book"],
                "market_status":"EXACT_TWO_SIDED_MARKET_AVAILABLE",
            })
        full_board.append(fg_row)

        # Team-total model board: two rows per game regardless of derivative market availability.
        for label, vals, team_display, team_model, hoa, state_obj, resolution in (
            ("home_team_total",sim.home_points,home_display,home_model,"HOME",h,hmeth),
            ("away_team_total",sim.away_points,away_display,away_model,"AWAY",a,ameth),
        ):
            fair_line, _, _, _ = _fair_line_from_curve(curve_map[label])
            toffer = _best_market_offer(market, oid, "TEAM_TOTAL", [team_display, team_model])
            row={
                "model_rank":event_index,"aita_event_id":eid,"odds_event_id":oid if oid != "nan" else "",
                "matchup":f"{away_display} @ {home_display}","team":team_display,"team_model":team_model,"home_away":hoa,
                "model_mean_points":float(np.mean(vals)),"model_median_points":float(np.median(vals)),"model_fair_team_total":fair_line,
                "book_team_total":np.nan,"model_team_total_edge_points":np.nan,"p_over_book":np.nan,"p_under_book":np.nan,"p_push_book":np.nan,
                "model_lean":"MODEL_ONLY","model_over_fair_american":np.nan,"model_under_fair_american":np.nan,
                "best_over_price":np.nan,"best_over_book":"","best_under_price":np.nan,"best_under_book":"",
                "market_status":"MODEL_ONLY_NO_EXACT_MARKET","model_status":model_status,
                "state_source":state_obj.state_source or state_obj.opponent_adjustment_source or "CFBD_STATE",
                "entity_resolution":resolution,"simulation_converged":conv,"data_quality_flags":flag_text,
            }
            if toffer:
                po, pu, pp, poc, puc, lean = _lean_at_line(vals, toffer["point"])
                row.update({
                    "book_team_total":toffer["point"],"model_team_total_edge_points":fair_line-toffer["point"],
                    "p_over_book":po,"p_under_book":pu,"p_push_book":pp,"model_lean":lean,
                    "model_over_fair_american":probability_to_american(poc),"model_under_fair_american":probability_to_american(puc),
                    "best_over_price":toffer["best_over_price"],"best_over_book":toffer["best_over_book"],
                    "best_under_price":toffer["best_under_price"],"best_under_book":toffer["best_under_book"],
                    "market_status":"EXACT_TWO_SIDED_MARKET_AVAILABLE",
                })
            team_board.append(row)

        h1_fair, _, _, _ = _fair_line_from_curve(curve_map["first_half_total"])
        h1offer = _best_market_offer(market, oid, "H1_TOTAL")
        h1row={
            "model_rank":event_index,"aita_event_id":eid,"odds_event_id":oid if oid != "nan" else "",
            "matchup":f"{away_display} @ {home_display}","away_team":away_display,"home_team":home_display,
            "model_mean_h1_total":float(np.mean(sim.h1_total)),"model_median_h1_total":float(np.median(sim.h1_total)),
            "model_fair_h1_total":h1_fair,"book_h1_total":np.nan,"model_h1_edge_points":np.nan,
            "p_over_book":np.nan,"p_under_book":np.nan,"p_push_book":np.nan,"model_lean":"MODEL_ONLY",
            "model_over_fair_american":np.nan,"model_under_fair_american":np.nan,"best_over_price":np.nan,"best_over_book":"",
            "best_under_price":np.nan,"best_under_book":"","market_status":"MODEL_ONLY_NO_EXACT_MARKET",
            "model_status":model_status,"simulation_converged":conv,"data_quality_flags":flag_text,
        }
        if h1offer:
            po, pu, pp, poc, puc, lean = _lean_at_line(sim.h1_total, h1offer["point"])
            h1row.update({
                "book_h1_total":h1offer["point"],"model_h1_edge_points":h1_fair-h1offer["point"],
                "p_over_book":po,"p_under_book":pu,"p_push_book":pp,"model_lean":lean,
                "model_over_fair_american":probability_to_american(poc),"model_under_fair_american":probability_to_american(puc),
                "best_over_price":h1offer["best_over_price"],"best_over_book":h1offer["best_over_book"],
                "best_under_price":h1offer["best_under_price"],"best_under_book":h1offer["best_under_book"],
                "market_status":"EXACT_TWO_SIDED_MARKET_AVAILABLE",
            })
        h1_board.append(h1row)
        dq.append({"aita_event_id":eid,"matchup":f"{away_display} @ {home_display}","flags":flags,"status":"WARN" if flags else "PASS"})

    # Exact-price EV layer. This is intentionally separate from the all-game model boards.
    for _, r in market.iterrows():
        match = slate[slate.get("odds_event_id", pd.Series(index=slate.index,dtype=str)).astype(str) == str(r.odds_event_id)] if "odds_event_id" in slate.columns else pd.DataFrame()
        if match.empty:
            continue
        ev=match.iloc[0]; eid=str(ev.get("aita_event_id") or ev.get("odds_event_id")); sim=sim_store.get(eid); ctx=ctx_store.get(eid)
        if sim is None or ctx is None:
            continue
        h,a=ctx["home"],ctx["away"]
        vals=_distribution_for(r,sim,home_display=ctx["home_display"],away_display=ctx["away_display"],home_model=ctx["home_model"],away_model=ctx["away_model"])
        if vals is None or pd.isna(r.point):
            continue
        p_mc,push=prob_at_line(vals,float(r.point),str(r.side))
        p_mc_cond = p_mc/max(1e-12,1-push)
        conv_row=next((x for x in convergence if x["aita_event_id"]==eid),None); converged=bool(conv_row and conv_row["converged"])
        stale=False
        try:
            lu=pd.to_datetime(r.get("last_update"),utc=True); st=pd.to_datetime(r.get("snapshot_time"),utc=True)
            stale=((st-lu).total_seconds()/60.0) > float(cfg.get("odds.stale_minutes",30))
        except Exception:
            pass
        conf=score_confidence(
            h,a,converged=converged,market_pair=True,weather_available=eid in weather_by_event,early_season=early,
            model_market_gap_pp=100*(p_mc_cond-float(r.P_MARKET_FAIR)),historical_calibration=historical_calibration_prior,
            entity_quality=.55 if ctx["fallback"] else 1.0,
        )
        w=_model_weight(cfg,early,conf.score); cs=_conservative_strength(conf.score,cfg)
        metrics=price_candidate(p_mc_cond,float(r.P_MARKET_FAIR),float(r.american_price),w,cs,p_push=push)
        blocked=(not converged) or stale
        g=quant_grade(metrics["EV_CONSERVATIVE"],conf.score,blocked,cfg)
        stake=stake_support(metrics["KELLY_FULL_CONSERVATIVE"],cfg)
        if not allow_stakes:
            stake["recommended_fractional_kelly_input"] = 0.0
            stake["max_stake_tier"] = "CALIBRATION_ONLY"
        d=r.to_dict(); d.update(metrics); d.update(stake)
        d.update({
            "aita_event_id":eid,"matchup":f"{ctx['away_display']} @ {ctx['home_display']}","p_push":push,"model_weight":w,
            "confidence":conf.score,"confidence_band":conf.band,"quant_grade":g,"grade_status":ev_estimate_status,
            "blocking_flag":blocked,"odds_stale":stale,"calibration_status":calibration_status,
            "ev_estimate_status":ev_estimate_status,
            "ev_actionability":"EXTERNAL_TRADING_AGENT_REVIEW_REQUIRED" if calibration_status == "CALIBRATED" else "RESEARCH_ONLY_UNTIL_CALIBRATED",
            "stake_status":"ENABLED" if allow_stakes else "DISABLED_UNTIL_CALIBRATED",
        })
        priced.append(d)
        conf_rows.append({"aita_event_id":eid,"market_family":r.market_family,"team_if_applicable":r.team_if_applicable,"side":r.side,"point":r.point,"confidence":conf.score,"band":conf.band,"calibration_status":calibration_status,**{f"component_{k}":v for k,v in conf.components.items()}})
        driver_rows.append({
            "aita_event_id":eid,"market_family":r.market_family,"side":r.side,"point":r.point,
            "edge_driver_1":f"model-vs-market probability {100*(p_mc_cond-float(r.P_MARKET_FAIR)):+.2f}pp",
            "edge_driver_2":f"home offense/away defense PPD delta {h.offense_ppd-a.defense_ppd_allowed:+.3f}; away offense/home defense {a.offense_ppd-h.defense_ppd_allowed:+.3f}",
            "edge_driver_3":f"projected total {np.mean(sim.total):.2f}; combined possessions {np.mean(sim.home_possessions+sim.away_possessions):.2f}",
            "risk_driver_1":f"mean latent sigma {(h.offense_sigma+h.defense_sigma+a.offense_sigma+a.defense_sigma)/4:.3f}; roster continuity {(h.roster_continuity+a.roster_continuity)/2:.3f}",
            "risk_driver_2":("early-season shrinkage active" if early else "mature-season blend") + ("; weather unavailable" if eid not in weather_by_event else "; weather loaded") + ("; sparse fallback prior used" if ctx["fallback"] else ""),
            "calibration_status":calibration_status,
        })
        indicators[f"{eid}|{r.market_family}|{r.get('team_if_applicable') or ''}|{r.side}|{r.point}"] = (vals > float(r.point)) if str(r.side)=="OVER" else (vals < float(r.point))

    master=_with_schema(pd.DataFrame(priced), EV_BOARD_COLUMNS)
    if not master.empty:
        master=master.sort_values(["EV_CONSERVATIVE","confidence"],ascending=[False,False]).reset_index(drop=True)
        master["quant_rank"]=np.arange(1,len(master)+1)
        master=_with_schema(master, EV_BOARD_COLUMNS)
    proj=pd.DataFrame(projections)
    dists=pd.DataFrame(dist_rows)
    fair_curve_df=pd.DataFrame(fair_curves)
    conf_df=pd.DataFrame(conf_rows)
    drivers=pd.DataFrame(driver_rows)
    fg=_with_schema(pd.DataFrame(full_board), FULL_BOARD_COLUMNS)
    tt=_with_schema(pd.DataFrame(team_board), TEAM_BOARD_COLUMNS)
    h1=_with_schema(pd.DataFrame(h1_board), H1_BOARD_COLUMNS)
    corr=indicator_correlation(indicators)
    risk_cols=[c for c in ["quant_rank","aita_event_id","market_family","team_if_applicable","side","point","recommended_fractional_kelly_input","max_stake_tier","confidence","quant_grade","calibration_status","stake_status"] if c in master.columns]
    risk=master[risk_cols].copy() if len(master) else pd.DataFrame(columns=risk_cols)
    if not risk.empty:
        risk["same_game_exposure"]="REVIEW_BY_TRADING_AGENT"; risk["correlation_cluster"]="SEE_11_CORRELATION_MATRIX.csv"

    def csv(df,name):
        df.to_csv(run_dir/name,index=False)

    csv(master,"02_MASTER_EV_BOARD.csv"); csv(fg,"03_FULL_GAME_TOTALS_BOARD.csv"); csv(tt,"04_TEAM_TOTALS_BOARD.csv"); csv(h1,"05_FIRST_HALF_TOTALS_BOARD.csv")
    csv(proj,"06_GAME_PROJECTIONS.csv"); csv(dists,"07_MONTE_CARLO_DISTRIBUTIONS.csv"); csv(market,"08_MARKET_SNAPSHOT.csv"); csv(conf_df,"09_MODEL_CONFIDENCE.csv"); csv(drivers,"10_EDGE_DRIVERS.csv")
    corr.to_csv(run_dir/"11_CORRELATION_MATRIX.csv"); csv(risk,"12_RISK_BOARD.csv"); csv(fair_curve_df,"18_FAIR_PRICE_CURVES.csv")
    pd.DataFrame(convergence).to_csv(run_dir/"17_MC_CONVERGENCE_REPORT.csv",index=False)
    ledger_src=Path(usage_ledger_path) if usage_ledger_path else None
    if ledger_src and ledger_src.exists(): shutil.copy2(ledger_src,run_dir/"16_ODDS_API_USAGE_LEDGER.csv")
    else: pd.DataFrame(columns=["timestamp","endpoint","sport","markets","regions_bookmakers","event_id","cost_last","credits_used","credits_remaining","run_id"]).to_csv(run_dir/"16_ODDS_API_USAGE_LEDGER.csv",index=False)

    blocking_events=sum(x["status"]=="BLOCK" for x in dq)
    warning_events=sum(x["status"]=="WARN" for x in dq)
    modeled_events=len(proj); total_events=len(slate)
    dq_status="BLOCK" if blocking_events else ("PASS_WITH_WARNINGS" if warning_events else "PASS")
    write_json(run_dir/"13_DATA_QUALITY_REPORT.json", {
        "run_id":run_id,"events":dq,"blocking_events":blocking_events,"warning_events":warning_events,
        "slate_events":total_events,"modeled_events":modeled_events,"model_coverage_pct":round(100*modeled_events/max(1,total_events),2),
        "policy":"MODEL_BOARDS_USE_HIGH_UNCERTAINTY_FALLBACK_PRIORS; EV_REQUIRES_EXACT_TWO_SIDED_MARKET",
    })
    write_json(run_dir/"14_MODEL_CARD.json", {
        "model_version":cfg.get("model_version"),"feature_version":cfg.get("feature_version"),
        "simulation_engine":"sequential possession/drive outcome Monte Carlo","primary_markets":["FG_TOTAL","TEAM_TOTAL","H1_TOTAL"],
        "pure_model_uses_market_line_as_feature":False,"trading_agent_embedded":False,"postgame_audit_embedded":False,
        "early_season_mode":early,"calibration_status":calibration_status,"ev_estimate_status":ev_estimate_status,
        "all_game_model_board_policy":True,
        "limitations":[
            "Sparse or unresolved teams use a dynamic high-uncertainty prior and are explicitly flagged",
            "Missing weather/QB data lowers confidence but does not suppress model-only projections",
            "EV estimates are not empirically validated until calibration status is promoted",
            "Market coverage varies by bookmaker/event and EV is never fabricated without an exact two-sided price",
            "ESPN endpoints are unofficial and adapter schema checks are mandatory",
        ],
    })
    write_json(run_dir/"15_RUN_AUDIT.json", {
        "run_id":run_id,"created_at":utc_now_iso(),"record_type":"PRE_GAME_PIPELINE_VALIDATION_ONLY",
        "postgame_grading_performed":False,"close_capture_performed":False,"simulation_count":n,"seed":cfg.get("simulation.seed"),
        "slate_event_count":total_events,"modeled_event_count":modeled_events,"priced_candidate_count":len(master),
        "calibration_status":calibration_status,"external_trading_agent_required":True,"historical_outputs_immutable":True,
    })
    manifest={
        "sport":"NCAAF","season":season,"week":week,"slate_date":slate_date,"run_id":run_id,
        "model_version":cfg.get("model_version"),"pipeline_version":cfg.get("pipeline_version"),"feature_version":cfg.get("feature_version"),
        "created_at":utc_now_iso(),"markets":["full_game_total","home_team_total","away_team_total","first_half_total"],
        "handoff_target":"external_ncaaf_trading_agent","trading_agent_embedded":False,"postgame_audit_embedded":False,
        "simulation_seed":cfg.get("simulation.seed"),"simulation_count":n,"early_season_mode":early,
        "data_quality_status":dq_status,"model_coverage":{"slate_events":total_events,"modeled_events":modeled_events,"pct":round(100*modeled_events/max(1,total_events),2)},
        "calibration_status":calibration_status,"ev_estimate_status":ev_estimate_status,
        "ev_policy":"EV requires exact two-sided sportsbook market; no market means model-only board, never fabricated EV",
        "warnings":["EV estimates are provisional/uncalibrated"] if calibration_status != "CALIBRATED" else [],"files":[],
    }
    write_json(run_dir/"00_MANIFEST.json",manifest)
    render_markdown(master,fg,tt,h1,run_dir/"01_NCAAF_FINAL_BOARDS.md",manifest)
    zip_path=Path(output_root)/f"NCAAF_MONTE_TOTALS_{season}_W{week:02d}_TRADING_AGENT_HANDOFF_{run_id[-10:]}.zip"
    return build_zip(run_dir,zip_path)
