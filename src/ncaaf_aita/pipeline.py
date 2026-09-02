from __future__ import annotations

import json
import math
import os
import shutil
from pathlib import Path
from uuid import uuid4
import numpy as np
import pandas as pd

from ncaaf_aita.common import utc_now_iso, write_json, stable_int_hash
from ncaaf_aita.config import Config
from ncaaf_aita.features.state import TeamState, WeatherState
from ncaaf_aita.simulation.engine import MonteCarloEngine, GameSimulationResult
from ncaaf_aita.pricing.curves import prob_at_line, curve
from ncaaf_aita.pricing.odds_math import vig_free_two_way
from ncaaf_aita.ev.engine import price_candidate
from ncaaf_aita.confidence.engine import score_confidence
from ncaaf_aita.correlation.engine import indicator_correlation
from ncaaf_aita.risk_support.engine import quant_grade, stake_support
from ncaaf_aita.reporting.boards import render_markdown
from ncaaf_aita.handoff.builder import build_zip


def _model_weight(cfg: Config, early: bool, conf: float):
    if conf < 65: return cfg.get("blend.low_confidence_model_weight", .45)
    return cfg.get("blend.early_season_model_weight", .55) if early else cfg.get("blend.mature_model_weight", .72)


def _conservative_strength(conf: float, cfg: Config):
    floor = cfg.get("blend.conservative_shrink_floor", .35)
    return floor + (1-floor)*max(0.0, min(1.0, (conf-50)/50))


def _pair_market_fair(market: pd.DataFrame) -> pd.DataFrame:
    if market.empty: return market
    keys = ["odds_event_id","market_family","period","team_if_applicable","point","bookmaker","bookmaker_title"]
    rows = []
    for _, g in market.groupby(keys, dropna=False):
        over = g[g.side == "OVER"]; under = g[g.side == "UNDER"]
        if over.empty or under.empty: continue
        ro, ru = over.iloc[0], under.iloc[0]
        try: po, pu, vig = vig_free_two_way(float(ro.american_price), float(ru.american_price))
        except Exception: continue
        for r, p in ((ro,po),(ru,pu)):
            d = r.to_dict(); d["P_MARKET_FAIR"] = p; d["vig"] = vig; rows.append(d)
    return pd.DataFrame(rows)


def _distribution_for(row, sim: GameSimulationResult, home: str, away: str):
    fam = row["market_family"]
    if fam == "FG_TOTAL": return sim.total
    if fam == "H1_TOTAL": return sim.h1_total
    if fam == "TEAM_TOTAL":
        team = row.get("team_if_applicable")
        if team == home: return sim.home_points
        if team == away: return sim.away_points
    return None



def model_first_shortlist(*, cfg: Config, slate: pd.DataFrame, team_states: pd.DataFrame, full_totals_market: pd.DataFrame, max_events: int | None = None, simulation_count: int | None = None, weather_by_event: dict | None = None) -> pd.DataFrame:
    """Run a pure football prescreen before any derivative-market call.

    The sportsbook total is used only *after* pure simulations as a comparison/shortlisting input;
    it never enters the football simulation.
    """
    state_map = {str(r["team"]): TeamState.from_row(r) for _, r in team_states.iterrows()}
    weather_by_event = weather_by_event or {}
    k = int(max_events or cfg.get("odds.max_derivative_events_per_run", 12))
    n = int(simulation_count or min(50000, cfg.get("simulation.production_count", 100000)))
    lines = full_totals_market[full_totals_market["market_family"] == "FG_TOTAL"].copy() if not full_totals_market.empty else pd.DataFrame()
    rows=[]
    for _, ev in slate.iterrows():
        eid=str(ev.get("aita_event_id") or ev.get("odds_event_id") or ev.get("espn_event_id"))
        oid=str(ev.get("odds_event_id") or "")
        home,away=str(ev.get("home_team")),str(ev.get("away_team"))
        if home not in state_map or away not in state_map or not oid or oid == "nan":
            continue
        wraw = weather_by_event.get(eid)
        weather = WeatherState(**wraw) if isinstance(wraw, dict) else None
        sim=MonteCarloEngine(seed=int(cfg.get("simulation.seed",20260901)) + stable_int_hash(eid)).simulate(
            state_map[home], state_map[away], n, weather, bool(ev.get("neutral_site",False)))
        g=lines[lines.odds_event_id.astype(str)==oid] if not lines.empty else pd.DataFrame()
        market_line=float(pd.to_numeric(g.get("point"), errors="coerce").dropna().median()) if not g.empty else float("nan")
        mean_total=float(np.mean(sim.total)); h1=float(np.mean(sim.h1_total)); home_pts=float(np.mean(sim.home_points)); away_pts=float(np.mean(sim.away_points))
        disagreement=abs(mean_total-market_line) if np.isfinite(market_line) else 0.0
        asymmetry=abs(home_pts-away_pts)
        h1_structure=abs(h1 - 0.5*mean_total)
        h,a=state_map[home],state_map[away]
        uncertainty=(h.offense_sigma+h.defense_sigma+a.offense_sigma+a.defense_sigma)/4
        continuity=(h.qb_continuity+a.qb_continuity+h.roster_continuity+a.roster_continuity)/4
        # High disagreement + structural derivative signal + continuity, penalized for uncertainty.
        score=(1.25*disagreement + .18*asymmetry + 1.5*h1_structure) * (0.65+0.35*continuity) * max(.35,1.0-uncertainty)
        rows.append({"aita_event_id":eid,"odds_event_id":oid,"matchup":f"{away} @ {home}","model_mean_total":mean_total,"market_total":market_line,"model_market_abs_gap":disagreement,"team_scoring_asymmetry":asymmetry,"h1_structural_difference":h1_structure,"uncertainty":uncertainty,"continuity":continuity,"derivative_interest_score":score})
    out=pd.DataFrame(rows)
    if out.empty: return out
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
    weather_by_event = weather_by_event or {}
    market = _pair_market_fair(market.copy())

    projections=[]; dist_rows=[]; fair_curves=[]; priced=[]; conf_rows=[]; driver_rows=[]; dq=[]; convergence=[]; indicators={}
    sim_store={}
    for _, ev in slate.iterrows():
        eid = str(ev.get("aita_event_id") or ev.get("odds_event_id") or ev.get("espn_event_id"))
        home, away = str(ev["home_team"]), str(ev["away_team"])
        flags=[]
        if home not in state_map: flags.append(("MISSING_TEAM_STATE_HOME","BLOCK"))
        if away not in state_map: flags.append(("MISSING_TEAM_STATE_AWAY","BLOCK"))
        if flags:
            dq.append({"aita_event_id":eid,"matchup":f"{away} @ {home}","flags":flags,"status":"BLOCK"}); continue
        h,a = state_map[home], state_map[away]
        if not h.roster_known or not a.roster_known: flags.append(("MISSING_ROSTER","WARN"))
        if not h.qb_known or not a.qb_known: flags.append(("MISSING_QB","WARN"))
        if not h.pbp_known or not a.pbp_known: flags.append(("MISSING_PBP","WARN"))
        if h.sample_size < 2 or a.sample_size < 2: flags.append(("LOW_SAMPLE","WARN"))
        if h.fcs_data_sparse or a.fcs_data_sparse: flags.append(("FCS_DATA_SPARSE","WARN"))
        if eid not in weather_by_event: flags.append(("WEATHER_UNAVAILABLE","WARN"))
        if "odds_event_id" in ev and (pd.isna(ev.get("odds_event_id")) or str(ev.get("odds_event_id")) in ("","nan")):
            flags.append(("EVENT_MAPPING_FAILED","BLOCK"))
        wraw = weather_by_event.get(eid)
        weather = WeatherState(**wraw) if isinstance(wraw, dict) else None
        engine = MonteCarloEngine(seed=int(cfg.get("simulation.seed",20260901)) + stable_int_hash(eid))
        sim = engine.simulate(h,a,n,weather,bool(ev.get("neutral_site",False)))
        sim_store[eid]=sim
        # Convergence compares increasing nested sample sizes on a representative central total.
        central = round(float(np.median(sim.total))*2)/2
        if n >= 500000:
            sample_a, sample_b = 250000, 500000
        elif n >= 250000:
            sample_a, sample_b = 100000, 250000
        else:
            sample_b = n
            sample_a = max(1000, n//2)
        p_a = float(np.mean(sim.total[:sample_a] > central)); p_b=float(np.mean(sim.total[:sample_b] > central))
        delta=abs(p_a-p_b); conv = delta <= cfg.get("simulation.convergence_tolerance",.0075)
        convergence.append({"aita_event_id":eid,"line":central,"sample_a":sample_a,"sample_b":sample_b,"p_sample_a":p_a,"p_sample_b":p_b,"abs_delta":delta,"tolerance":cfg.get("simulation.convergence_tolerance",.0075),"converged":conv})
        if not conv: flags.append(("SIMULATION_NOT_CONVERGED","BLOCK"))
        projections.append({
            "aita_event_id":eid,"matchup":f"{away} @ {home}","home_team":home,"away_team":away,
            "mean_home_points":float(np.mean(sim.home_points)),"median_home_points":float(np.median(sim.home_points)),
            "mean_away_points":float(np.mean(sim.away_points)),"median_away_points":float(np.median(sim.away_points)),
            "mean_total":float(np.mean(sim.total)),"median_total":float(np.median(sim.total)),
            "mean_margin":float(np.mean(sim.home_points-sim.away_points)),"first_half_mean_total":float(np.mean(sim.h1_total)),
            "first_half_median_total":float(np.median(sim.h1_total)),"p10_total":float(np.quantile(sim.total,.10)),"p25_total":float(np.quantile(sim.total,.25)),
            "p75_total":float(np.quantile(sim.total,.75)),"p90_total":float(np.quantile(sim.total,.90)),
            "mean_possessions_home":float(np.mean(sim.home_possessions)),"mean_possessions_away":float(np.mean(sim.away_possessions)),
            "median_margin":float(np.median(sim.home_points-sim.away_points)),
            "p_home_win":float(np.mean(sim.home_points>sim.away_points)),"p_away_win":float(np.mean(sim.away_points>sim.home_points)),"p_tie":float(np.mean(sim.home_points==sim.away_points)),
        })
        fg_lines=np.arange(float(cfg.get("simulation.total_curve_min",30.5)),float(cfg.get("simulation.total_curve_max",90.5))+1e-9,float(cfg.get("simulation.total_curve_step",1.0)))
        tt_lines=np.arange(float(cfg.get("simulation.team_total_min",7.5)),float(cfg.get("simulation.team_total_max",60.5))+1e-9,float(cfg.get("simulation.team_total_step",1.0)))
        h1_lines=np.arange(float(cfg.get("simulation.h1_total_min",14.5)),float(cfg.get("simulation.h1_total_max",48.5))+1e-9,float(cfg.get("simulation.h1_total_step",1.0)))
        for fam,label,vals,team_name,lineset in (
            ("FG_TOTAL","full_game_total",sim.total,None,fg_lines),
            ("TEAM_TOTAL","home_team_total",sim.home_points,home,tt_lines),
            ("TEAM_TOTAL","away_team_total",sim.away_points,away,tt_lines),
            ("H1_TOTAL","first_half_total",sim.h1_total,None,h1_lines),
        ):
            c=curve(vals,lineset,label)
            c.insert(0,"aita_event_id",eid); c.insert(1,"market_family",fam); c.insert(2,"team_if_applicable",team_name)
            fair_curves.extend(c.to_dict("records"))
        for q in (.05,.10,.25,.50,.75,.90,.95):
            dist_rows.append({"aita_event_id":eid,"quantile":q,"home_points":float(np.quantile(sim.home_points,q)),"away_points":float(np.quantile(sim.away_points,q)),"total":float(np.quantile(sim.total,q)),"h1_total":float(np.quantile(sim.h1_total,q))})
        dq.append({"aita_event_id":eid,"matchup":f"{away} @ {home}","flags":flags,"status":"BLOCK" if any(s=="BLOCK" for _,s in flags) else "PASS"})

    for _, r in market.iterrows():
        # map Odds API id from slate
        match = slate[slate.get("odds_event_id", pd.Series(index=slate.index,dtype=str)).astype(str) == str(r.odds_event_id)] if "odds_event_id" in slate.columns else pd.DataFrame()
        if match.empty: continue
        ev=match.iloc[0]; eid=str(ev.get("aita_event_id") or ev.get("odds_event_id")); sim=sim_store.get(eid)
        if sim is None: continue
        home, away=str(ev.home_team), str(ev.away_team)
        vals=_distribution_for(r,sim,home,away)
        if vals is None or pd.isna(r.point): continue
        p_mc,push=prob_at_line(vals,float(r.point),str(r.side))
        # push-adjust fair win probability for integer lines; exact EV still treats push as no loss, handled conservatively by normalization here.
        p_mc_cond = p_mc/max(1e-12,1-push)
        h,a=state_map[home],state_map[away]
        conv_row=next((x for x in convergence if x["aita_event_id"]==eid),None); converged=bool(conv_row and conv_row["converged"])
        stale=False
        try:
            lu=pd.to_datetime(r.get("last_update"),utc=True); st=pd.to_datetime(r.get("snapshot_time"),utc=True)
            stale=((st-lu).total_seconds()/60.0) > float(cfg.get("odds.stale_minutes",30))
        except Exception:
            pass
        conf=score_confidence(h,a,converged=converged,market_pair=True,weather_available=eid in weather_by_event,early_season=early,model_market_gap_pp=100*(p_mc_cond-float(r.P_MARKET_FAIR)))
        w=_model_weight(cfg,early,conf.score); cs=_conservative_strength(conf.score,cfg)
        metrics=price_candidate(p_mc_cond,float(r.P_MARKET_FAIR),float(r.american_price),w,cs,p_push=push)
        blocked=(not converged) or stale
        g=quant_grade(metrics["EV_CONSERVATIVE"],conf.score,blocked,cfg)
        stake=stake_support(metrics["KELLY_FULL_CONSERVATIVE"],cfg)
        d=r.to_dict(); d.update(metrics); d.update(stake)
        d.update({"aita_event_id":eid,"matchup":f"{away} @ {home}","p_push":push,"model_weight":w,"confidence":conf.score,"confidence_band":conf.band,"quant_grade":g,"blocking_flag":blocked,"odds_stale":stale})
        priced.append(d)
        conf_rows.append({"aita_event_id":eid,"market_family":r.market_family,"team_if_applicable":r.team_if_applicable,"side":r.side,"point":r.point,"confidence":conf.score,"band":conf.band,**{f"component_{k}":v for k,v in conf.components.items()}})
        # Edge driver layer derives from actual feature deltas.
        offense_edge=(h.offense_ppd-a.defense_ppd_allowed) if r.get("team_if_applicable") in (None,home) else (a.offense_ppd-h.defense_ppd_allowed)
        driver_rows.append({"aita_event_id":eid,"market_family":r.market_family,"side":r.side,"point":r.point,
            "edge_driver_1":f"model-vs-market probability {100*(p_mc_cond-float(r.P_MARKET_FAIR)):+.2f}pp",
            "edge_driver_2":f"home offense/away defense PPD delta {h.offense_ppd-a.defense_ppd_allowed:+.3f}; away offense/home defense {a.offense_ppd-h.defense_ppd_allowed:+.3f}",
            "edge_driver_3":f"projected total {np.mean(sim.total):.2f}; combined possessions {np.mean(sim.home_possessions+sim.away_possessions):.2f}",
            "risk_driver_1":f"mean latent sigma {(h.offense_sigma+h.defense_sigma+a.offense_sigma+a.defense_sigma)/4:.3f}; roster continuity {(h.roster_continuity+a.roster_continuity)/2:.3f}",
            "risk_driver_2":("early-season shrinkage active" if early else "mature-season blend") + ("; weather unavailable" if eid not in weather_by_event else "; weather loaded")})
        indicators[f"{eid}|{r.market_family}|{r.get('team_if_applicable') or ''}|{r.side}|{r.point}"] = (vals > float(r.point)) if str(r.side)=="OVER" else (vals < float(r.point))

    master=pd.DataFrame(priced)
    if not master.empty:
        master=master.sort_values(["EV_CONSERVATIVE","confidence"],ascending=[False,False]).reset_index(drop=True)
        master["quant_rank"]=np.arange(1,len(master)+1)
    proj=pd.DataFrame(projections); dists=pd.DataFrame(dist_rows); fair_curve_df=pd.DataFrame(fair_curves); conf_df=pd.DataFrame(conf_rows); drivers=pd.DataFrame(driver_rows)
    corr=indicator_correlation(indicators)
    risk_cols=[c for c in ["quant_rank","aita_event_id","market_family","team_if_applicable","side","point","recommended_fractional_kelly_input","max_stake_tier","confidence","quant_grade"] if c in master.columns]
    risk=master[risk_cols].copy() if not master.empty else pd.DataFrame(columns=risk_cols)
    if not risk.empty:
        risk["same_game_exposure"]="REVIEW_BY_TRADING_AGENT"; risk["correlation_cluster"]="SEE_11_CORRELATION_MATRIX.csv"
    fg=master[master.market_family=="FG_TOTAL"].copy() if not master.empty else pd.DataFrame()
    tt=master[master.market_family=="TEAM_TOTAL"].copy() if not master.empty else pd.DataFrame()
    h1=master[master.market_family=="H1_TOTAL"].copy() if not master.empty else pd.DataFrame()

    # Output files.
    def csv(df,name): df.to_csv(run_dir/name,index=False)
    csv(master,"02_MASTER_EV_BOARD.csv"); csv(fg,"03_FULL_GAME_TOTALS_BOARD.csv"); csv(tt,"04_TEAM_TOTALS_BOARD.csv"); csv(h1,"05_FIRST_HALF_TOTALS_BOARD.csv")
    csv(proj,"06_GAME_PROJECTIONS.csv"); csv(dists,"07_MONTE_CARLO_DISTRIBUTIONS.csv"); csv(market,"08_MARKET_SNAPSHOT.csv"); csv(conf_df,"09_MODEL_CONFIDENCE.csv"); csv(drivers,"10_EDGE_DRIVERS.csv")
    corr.to_csv(run_dir/"11_CORRELATION_MATRIX.csv"); csv(risk,"12_RISK_BOARD.csv"); csv(fair_curve_df,"18_FAIR_PRICE_CURVES.csv")
    pd.DataFrame(convergence).to_csv(run_dir/"17_MC_CONVERGENCE_REPORT.csv",index=False)
    ledger_src=Path(usage_ledger_path) if usage_ledger_path else None
    if ledger_src and ledger_src.exists(): shutil.copy2(ledger_src,run_dir/"16_ODDS_API_USAGE_LEDGER.csv")
    else: pd.DataFrame(columns=["timestamp","endpoint","sport","markets","regions_bookmakers","event_id","cost_last","credits_used","credits_remaining","run_id"]).to_csv(run_dir/"16_ODDS_API_USAGE_LEDGER.csv",index=False)

    write_json(run_dir/"13_DATA_QUALITY_REPORT.json", {"run_id":run_id,"events":dq,"blocking_events":sum(x["status"]=="BLOCK" for x in dq)})
    write_json(run_dir/"14_MODEL_CARD.json", {"model_version":cfg.get("model_version"),"feature_version":cfg.get("feature_version"),"simulation_engine":"sequential possession/drive outcome Monte Carlo","primary_markets":["FG_TOTAL","TEAM_TOTAL","H1_TOTAL"],"pure_model_uses_market_line_as_feature":False,"trading_agent_embedded":False,"early_season_mode":early,"limitations":["Feature warehouse quality controls model quality","ESPN endpoints are unofficial and adapter schema checks are mandatory","Market coverage varies by bookmaker/event"]})
    write_json(run_dir/"15_RUN_AUDIT.json", {"run_id":run_id,"created_at":utc_now_iso(),"simulation_count":n,"seed":cfg.get("simulation.seed"),"priced_candidate_count":len(master),"external_trading_agent_required":True,"historical_outputs_immutable":True})
    manifest={"sport":"NCAAF","season":season,"week":week,"slate_date":slate_date,"run_id":run_id,"model_version":cfg.get("model_version"),"pipeline_version":cfg.get("pipeline_version"),"feature_version":cfg.get("feature_version"),"created_at":utc_now_iso(),"markets":["full_game_total","home_team_total","away_team_total","first_half_total"],"handoff_target":"external_ncaaf_trading_agent","trading_agent_embedded":False,"simulation_seed":cfg.get("simulation.seed"),"simulation_count":n,"early_season_mode":early,"data_quality_status":"BLOCK" if any(x["status"]=="BLOCK" for x in dq) else "PASS","warnings":[],"files":[]}
    write_json(run_dir/"00_MANIFEST.json",manifest)
    render_markdown(master,run_dir/"01_NCAAF_FINAL_BOARDS.md",manifest)
    zip_path=Path(output_root)/f"NCAAF_MONTE_TOTALS_{season}_W{week:02d}_TRADING_AGENT_HANDOFF_{run_id[-10:]}.zip"
    return build_zip(run_dir,zip_path)
