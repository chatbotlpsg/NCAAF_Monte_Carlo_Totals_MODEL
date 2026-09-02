from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pandas as pd

from ncaaf_aita import __version__
from ncaaf_aita.config import load_config
from ncaaf_aita.data.espn import EspnAdapter
from ncaaf_aita.data.odds import OddsApiAdapter, QuotaPolicy
from ncaaf_aita.data.cfbd import CfbdAdapter
from ncaaf_aita.data.weather import OpenMeteoAdapter
from ncaaf_aita.data.entities import norm_team
from ncaaf_aita.features.builders import build_team_states_from_cfbd_plays, enrich_with_core, build_preseason_states_from_prior_ratings, blend_with_preseason_prior
from ncaaf_aita.pipeline import run_quant_pipeline, model_first_shortlist


def _load_env(path=".env"):
    p=Path(path)
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line=line.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            k,v=line.split("=",1); os.environ.setdefault(k.strip(),v.strip())


def doctor(cfg):
    checks={
        "version":__version__,
        "python_boundary_ok":not Path("src/ncaaf_aita/trading_agent").exists(),
        "odds_api_key_present":bool(os.getenv("ODDS_API_KEY")),
        "cfbd_api_key_present":bool(os.getenv("CFBD_API_KEY")),
        "approved_markets":cfg.get("odds.approved_slate_markets",[])+cfg.get("odds.approved_derivative_markets",[]),
        "trading_agent_embedded":False,
    }
    print(json.dumps(checks,indent=2))
    return 0 if checks["python_boundary_ok"] else 2


def discover_slate(cfg,date):
    espn=EspnAdapter(cfg.get("sources.espn_base"))
    df=espn.normalize_scoreboard(espn.scoreboard(date.replace("-","")))
    key=os.getenv("ODDS_API_KEY")
    if key:
        odds=OddsApiAdapter(cfg.get("sources.odds_base"),key,region=cfg.get("odds.region","us"),bookmakers=cfg.get("odds.bookmakers",[]))
        oe=pd.DataFrame(odds.events())
        if not oe.empty:
            # Deterministic normalized home/away matching; unresolved rows remain blank and fail closed.
            df["odds_event_id"]=""
            oe=oe.copy(); oe["home_norm"]=oe.home_team.map(norm_team); oe["away_norm"]=oe.away_team.map(norm_team)
            for i,r in df.iterrows():
                cand=oe[(oe.home_norm==norm_team(r.home_team))&(oe.away_norm==norm_team(r.away_team))]
                if len(cand)==1: df.at[i,"odds_event_id"]=cand.iloc[0]["id"]
    df["aita_event_id"]=[f"AITA_{date}_{i:03d}" for i in range(1,len(df)+1)]
    out=Path("data/normalized/SLATE_EVENTS.csv"); out.parent.mkdir(parents=True,exist_ok=True); df.to_csv(out,index=False)
    print(out)


def _merge_roster_qb_context(df: pd.DataFrame) -> pd.DataFrame:
    cont=Path("data/features/ROSTER_CONTINUITY.csv")
    if cont.exists():
        rc=pd.read_csv(cont)
        if not rc.empty and "team" in rc:
            keep=[c for c in ["team","roster_continuity","roster_known"] if c in rc]
            df=df.merge(rc[keep],on="team",how="left",suffixes=("","_roster"))
            if "roster_continuity_roster" in df:
                df["roster_continuity"]=df["roster_continuity_roster"].combine_first(df.get("roster_continuity")); df=df.drop(columns=["roster_continuity_roster"])
            if "roster_known_roster" in df:
                df["roster_known"]=df["roster_known_roster"].fillna(df.get("roster_known",False)); df=df.drop(columns=["roster_known_roster"])
    qb=Path("data/features/STARTER_QB_MAP.csv")
    if qb.exists():
        q=pd.read_csv(qb)
        if not q.empty and "team" in q:
            keep=[c for c in ["team","starter_qb_id","qb_returning_flag","qb_uncertainty"] if c in q]
            df=df.merge(q[keep],on="team",how="left")
            df["qb_known"]=df.get("starter_qb_id").notna()
            if "qb_returning_flag" in df:
                df["qb_continuity"]=pd.to_numeric(df["qb_returning_flag"],errors="coerce").combine_first(df.get("qb_continuity"))
            if "qb_uncertainty" in df:
                uq=pd.to_numeric(df["qb_uncertainty"],errors="coerce").fillna(.5).clip(0,1)
                df["offense_sigma"]=pd.to_numeric(df["offense_sigma"],errors="coerce")*(1+.25*uq)
    return df


def build_team_states(cfg,year,week):
    key=os.getenv("CFBD_API_KEY")
    if not key: raise SystemExit("CFBD_API_KEY missing")
    cfbd=CfbdAdapter(cfg.get("sources.cfbd_base"),key)
    prior_core=cfbd.core_ratings(year-1); prior_sp=cfbd.sp_ratings(year-1); prior_elo=cfbd.elo_ratings(year-1)
    prior=build_preseason_states_from_prior_ratings(prior_core,prior_sp,prior_elo)
    if week <= 1:
        df=prior
    else:
        plays=[]
        for w in range(1,week):
            plays.extend(cfbd.plays(year,w))
        current=build_team_states_from_cfbd_plays(plays,early_season=week<=3)
        try:
            current=enrich_with_core(current,cfbd.core_ratings(year),through_week_max=week-1)
        except Exception as exc:
            print(f"CORE_ENRICH_WARN: {exc}")
        df=blend_with_preseason_prior(current,prior,week=week)
    df=_merge_roster_qb_context(df)
    out=Path("data/features/TEAM_STATES.csv"); out.parent.mkdir(parents=True,exist_ok=True); df.to_csv(out,index=False); print(out)


def refresh_rosters(cfg, season: int, slate_path: str):
    slate=pd.read_csv(slate_path); espn=EspnAdapter(cfg.get("sources.espn_base"))
    rows=[]
    for side in ("home","away"):
        tid_col=f"espn_{side}_team_id"; team_col=f"{side}_team"
        if tid_col not in slate: continue
        for _,r in slate[[tid_col,team_col]].drop_duplicates().iterrows():
            tid=str(r[tid_col]); team=str(r[team_col])
            current=espn.normalize_roster(espn.roster(tid,season),tid,season)
            cdir=Path(f"data/normalized/rosters/{season}"); cdir.mkdir(parents=True,exist_ok=True); current.to_csv(cdir/f"{tid}.csv",index=False)
            prior=pd.DataFrame()
            try:
                prior=espn.normalize_roster(espn.roster(tid,season-1),tid,season-1)
                pdir=Path(f"data/normalized/rosters/{season-1}"); pdir.mkdir(parents=True,exist_ok=True); prior.to_csv(pdir/f"{tid}.csv",index=False)
            except Exception as exc:
                print(f"PRIOR_ROSTER_WARN {team}: {exc}")
            cur_ids=set(current.espn_athlete_id.dropna().astype(str)) if not current.empty else set()
            pri_ids=set(prior.espn_athlete_id.dropna().astype(str)) if not prior.empty else set()
            pct=len(cur_ids & pri_ids)/max(1,len(cur_ids)) if cur_ids else .5
            qbs=current[current.position.astype(str).str.upper().eq("QB")] if not current.empty and "position" in current else pd.DataFrame()
            rows.append({"team":team,"espn_team_id":tid,"roster_continuity":pct,"roster_known":not current.empty,"qb_candidate_count":len(qbs),"qb_candidates":"|".join(qbs.player_name.dropna().astype(str).tolist()) if not qbs.empty else ""})
    out=Path("data/features/ROSTER_CONTINUITY.csv"); out.parent.mkdir(parents=True,exist_ok=True); pd.DataFrame(rows).drop_duplicates("team").to_csv(out,index=False); print(out)


def load_weather_for_slate(cfg, slate: pd.DataFrame, stadiums_path: str | None):
    if not stadiums_path: return {}
    sp=Path(stadiums_path)
    if not sp.exists(): raise SystemExit(f"Stadium registry not found: {sp}")
    stadiums=pd.read_csv(sp); weather=OpenMeteoAdapter(cfg.get("sources.weather_base")); out={}
    for _,ev in slate.iterrows():
        eid=str(ev.get("aita_event_id") or ev.get("odds_event_id") or ev.get("espn_event_id")); venue=str(ev.get("venue") or "")
        m=stadiums[stadiums.venue.astype(str)==venue] if "venue" in stadiums else pd.DataFrame()
        if m.empty: continue
        rr=m.iloc[0]
        if pd.isna(rr.get("latitude")) or pd.isna(rr.get("longitude")) or pd.isna(ev.get("kickoff_utc")): continue
        try:
            w=weather.forecast(float(rr.latitude),float(rr.longitude),str(ev.kickoff_utc))
            if w: out[eid]=w
        except Exception as exc: print(f"WEATHER_WARN {venue}: {exc}")
    return out

def _demo_data():
    slate=pd.DataFrame([
        {"aita_event_id":"DEMO1","odds_event_id":"ODDS1","home_team":"Demo State","away_team":"AITA Tech","neutral_site":False},
        {"aita_event_id":"DEMO2","odds_event_id":"ODDS2","home_team":"Monte Carlo U","away_team":"Variance College","neutral_site":False},
    ])
    states=pd.DataFrame([
        {"team":"Demo State","offense_ppd":3.05,"defense_ppd_allowed":2.15,"possessions_mean":12.8,"possessions_sd":1.2,"td_share":.70,"fg_share":.19,"turnover_rate":.10,"explosive_rate":.15,"pass_rate":.54,"qb_continuity":.90,"roster_continuity":.76,"offense_sigma":.18,"defense_sigma":.16,"sample_size":3,"source_quality":.88,"roster_known":True,"qb_known":True,"pbp_known":True},
        {"team":"AITA Tech","offense_ppd":2.50,"defense_ppd_allowed":2.75,"possessions_mean":12.4,"possessions_sd":1.4,"td_share":.66,"fg_share":.21,"turnover_rate":.13,"explosive_rate":.12,"pass_rate":.48,"qb_continuity":.70,"roster_continuity":.66,"offense_sigma":.20,"defense_sigma":.20,"sample_size":3,"source_quality":.84,"roster_known":True,"qb_known":True,"pbp_known":True},
        {"team":"Monte Carlo U","offense_ppd":2.82,"defense_ppd_allowed":2.45,"possessions_mean":13.1,"possessions_sd":1.3,"td_share":.69,"fg_share":.20,"turnover_rate":.11,"explosive_rate":.14,"pass_rate":.52,"qb_continuity":.78,"roster_continuity":.72,"offense_sigma":.19,"defense_sigma":.18,"sample_size":3,"source_quality":.86,"roster_known":True,"qb_known":True,"pbp_known":True},
        {"team":"Variance College","offense_ppd":2.30,"defense_ppd_allowed":2.62,"possessions_mean":12.0,"possessions_sd":1.5,"td_share":.65,"fg_share":.22,"turnover_rate":.14,"explosive_rate":.10,"pass_rate":.46,"qb_continuity":.56,"roster_continuity":.60,"offense_sigma":.22,"defense_sigma":.22,"sample_size":3,"source_quality":.80,"roster_known":True,"qb_known":True,"pbp_known":True},
    ])
    rows=[]
    def add(eid,fam,team,line,over,under,book="draftkings"):
        for side,price in (("OVER",over),("UNDER",under)):
            rows.append({"odds_event_id":eid,"market_family":fam,"period":"H1" if fam=="H1_TOTAL" else "FG","team_if_applicable":team,"side":side,"point":line,"american_price":price,"bookmaker":book,"bookmaker_title":"DraftKings","last_update":"2026-09-01T20:00:00Z","snapshot_time":"2026-09-01T20:00:00Z"})
    add("ODDS1","FG_TOTAL",None,55.5,-110,-110); add("ODDS1","TEAM_TOTAL","Demo State",31.5,-105,-115); add("ODDS1","H1_TOTAL",None,27.5,-108,-112)
    add("ODDS2","FG_TOTAL",None,52.5,-110,-110); add("ODDS2","TEAM_TOTAL","Monte Carlo U",28.5,-110,-110); add("ODDS2","H1_TOTAL",None,25.5,-105,-115)
    return slate,states,pd.DataFrame(rows)


def main(argv=None):
    _load_env()
    p=argparse.ArgumentParser(prog="ncaaf-aita")
    p.add_argument("--config",default="configs/default.yaml")
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("doctor")
    d=sub.add_parser("discover-slate"); d.add_argument("--date",required=True)
    b=sub.add_parser("build-team-states"); b.add_argument("--year",type=int,required=True); b.add_argument("--week",type=int,required=True)
    rr=sub.add_parser("refresh-rosters"); rr.add_argument("--season",type=int,required=True); rr.add_argument("--slate",default="data/normalized/SLATE_EVENTS.csv")
    demo=sub.add_parser("demo"); demo.add_argument("--week",type=int,default=1); demo.add_argument("--slate-date",default="2026-09-05"); demo.add_argument("--simulations",type=int,default=30000)
    run=sub.add_parser("run"); run.add_argument("--season",type=int,required=True); run.add_argument("--week",type=int,required=True); run.add_argument("--slate-date",required=True); run.add_argument("--slate",required=True); run.add_argument("--team-states",required=True); run.add_argument("--market-file"); run.add_argument("--live-odds",action="store_true"); run.add_argument("--simulations",type=int); run.add_argument("--stadiums")
    close=sub.add_parser("capture-close"); close.add_argument("--master-board",required=True); close.add_argument("--label",default="CLOSE_PROXY_PUBLIC")
    audit=sub.add_parser("audit"); audit.add_argument("--master-board",required=True); audit.add_argument("--results",required=True); audit.add_argument("--close-snapshot"); audit.add_argument("--out-dir",default="data/audits/latest")
    args=p.parse_args(argv); cfg=load_config(args.config)
    if args.cmd=="doctor": return doctor(cfg)
    if args.cmd=="discover-slate": discover_slate(cfg,args.date); return 0
    if args.cmd=="build-team-states": build_team_states(cfg,args.year,args.week); return 0
    if args.cmd=="refresh-rosters": refresh_rosters(cfg,args.season,args.slate); return 0
    if args.cmd=="demo":
        slate,states,market=_demo_data(); z=run_quant_pipeline(cfg=cfg,slate=slate,team_states=states,market=market,season=2026,week=args.week,slate_date=args.slate_date,simulation_count=args.simulations); print(z); return 0
    if args.cmd=="audit":
        from ncaaf_aita.audit.post_slate import write_audit
        out=write_audit(args.master_board,args.results,args.out_dir,args.close_snapshot); print(out); return 0
    if args.cmd=="capture-close":
        key=os.getenv("ODDS_API_KEY")
        if not key: raise SystemExit("ODDS_API_KEY missing; close prices cannot be fabricated")
        board=pd.read_csv(args.master_board)
        odds=OddsApiAdapter(cfg.get("sources.odds_base"),key,region=cfg.get("odds.region","us"),bookmakers=cfg.get("odds.bookmakers",[]),policy=QuotaPolicy(cfg.get("odds.minimum_credits_remaining",100),cfg.get("odds.weekly_soft_budget",90),cfg.get("odds.monthly_soft_budget",400)))
        market=odds.normalize(odds.slate_totals())
        ids=board.get("odds_event_id",pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
        for eid in ids:
            fam=set(board.loc[board.odds_event_id.astype(str)==eid,"market_family"].astype(str))
            mk=[]
            if "TEAM_TOTAL" in fam: mk.append("team_totals")
            if "H1_TOTAL" in fam: mk.append("totals_h1")
            if mk:
                try: market=pd.concat([market,odds.normalize(odds.event_derivatives(eid,tuple(mk)))],ignore_index=True)
                except Exception as exc: print(f"CLOSE_CAPTURE_WARN {eid}: {exc}")
        from ncaaf_aita.common import utc_now_iso
        stamp=utc_now_iso().replace(":","-")
        out=Path("data/snapshots/close")/f"{stamp}_{args.label}.csv"; out.parent.mkdir(parents=True,exist_ok=True); market["snapshot_label"]=args.label; market.to_csv(out,index=False); print(out); return 0
    if args.cmd=="run":
        slate=pd.read_csv(args.slate); states=pd.read_csv(args.team_states); ledger=None
        if args.simulations is not None and args.simulations < int(cfg.get("simulation.production_count",100000)):
            raise SystemExit(f"Production run requires at least {cfg.get('simulation.production_count',100000)} simulations")
        weather_by_event=load_weather_for_slate(cfg,slate,args.stadiums)
        if args.live_odds:
            key=os.getenv("ODDS_API_KEY")
            if not key: raise SystemExit("ODDS_API_KEY missing; live odds cannot be fabricated")
            odds=OddsApiAdapter(cfg.get("sources.odds_base"),key,region=cfg.get("odds.region","us"),bookmakers=cfg.get("odds.bookmakers",[]),policy=QuotaPolicy(cfg.get("odds.minimum_credits_remaining",100),cfg.get("odds.weekly_soft_budget",90),cfg.get("odds.monthly_soft_budget",400)))
            raw=odds.slate_totals(); market=odds.normalize(raw); market["snapshot_label"]="ENTRY"
            shortlist=model_first_shortlist(cfg=cfg,slate=slate,team_states=states,full_totals_market=market,
                                            max_events=int(cfg.get("odds.max_derivative_events_per_run",12)),
                                            simulation_count=min(50000, int(args.simulations or cfg.get("simulation.production_count",100000))),
                                            weather_by_event=weather_by_event)
            Path("data/audits").mkdir(parents=True,exist_ok=True)
            shortlist.to_csv("data/audits/LATEST_DERIVATIVE_SHORTLIST.csv",index=False)
            print("MODEL_FIRST_DERIVATIVE_SHORTLIST")
            if not shortlist.empty:
                print(shortlist[["matchup","model_mean_total","market_total","derivative_interest_score"]].to_string(index=False))
            for eid in shortlist.get("odds_event_id",pd.Series(dtype=str)).astype(str).tolist():
                try: market=pd.concat([market,odds.normalize(odds.event_derivatives(eid)).assign(snapshot_label="ENTRY")],ignore_index=True)
                except Exception as exc: print(f"DERIVATIVE_SCAN_WARN {eid}: {exc}")
            ledger=odds.ledger
        else:
            if not args.market_file: raise SystemExit("Provide --market-file or --live-odds")
            market=pd.read_csv(args.market_file)
        z=run_quant_pipeline(cfg=cfg,slate=slate,team_states=states,market=market,season=args.season,week=args.week,slate_date=args.slate_date,simulation_count=args.simulations,weather_by_event=weather_by_event,usage_ledger_path=ledger); print(z); return 0

if __name__ == "__main__":
    raise SystemExit(main())
