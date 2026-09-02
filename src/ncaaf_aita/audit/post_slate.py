from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd
from ncaaf_aita.pricing.odds_math import american_to_break_even, american_to_profit_factor


def clv_probability_points(entry_odds: float, close_odds: float) -> float:
    # Positive means the closing market requires a higher break-even probability on our side.
    return 100*(american_to_break_even(close_odds) - american_to_break_even(entry_odds))


def _settled_value(row, result):
    fam=str(row["market_family"])
    if fam == "FG_TOTAL":
        return float(result.final_home_points + result.final_away_points)
    if fam == "H1_TOTAL":
        if pd.isna(result.get("h1_home_points")) or pd.isna(result.get("h1_away_points")): return np.nan
        return float(result.h1_home_points + result.h1_away_points)
    if fam == "TEAM_TOTAL":
        team=str(row.get("team_if_applicable"))
        if team == str(result.home_team): return float(result.final_home_points)
        if team == str(result.away_team): return float(result.final_away_points)
    return np.nan


def audit_board(master: pd.DataFrame, results: pd.DataFrame, close_market: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    out=[]
    close_market = close_market if close_market is not None else pd.DataFrame()
    for _, r in master.iterrows():
        rr=results[results.aita_event_id.astype(str)==str(r.aita_event_id)]
        if rr.empty: continue
        res=rr.iloc[0]; value=_settled_value(r,res)
        d=r.to_dict(); d["settled_value"]=value
        if pd.isna(value):
            d.update({"result":"UNGRADED","unit_pnl":np.nan})
        else:
            line=float(r.point); side=str(r.side).upper()
            if value == line: result="PUSH"; pnl=0.0
            else:
                win=(value>line) if side=="OVER" else (value<line)
                result="WIN" if win else "LOSS"; pnl=american_to_profit_factor(float(r.american_price)) if win else -1.0
            d.update({"result":result,"unit_pnl":pnl})
        d["close_price"]=np.nan; d["clv_probability_points"]=np.nan
        if not close_market.empty:
            keys=(
                close_market.odds_event_id.astype(str)==str(r.odds_event_id),
                close_market.market_family.astype(str)==str(r.market_family),
                close_market.side.astype(str)==str(r.side),
                pd.to_numeric(close_market.point,errors="coerce")==float(r.point),
            )
            m=close_market[keys[0]&keys[1]&keys[2]&keys[3]]
            if str(r.market_family)=="TEAM_TOTAL" and "team_if_applicable" in m:
                m=m[m.team_if_applicable.fillna("").astype(str)==str(r.get("team_if_applicable") or "")]
            if not m.empty:
                same=m[m.bookmaker.astype(str)==str(r.bookmaker)] if "bookmaker" in m else pd.DataFrame()
                c=(same if not same.empty else m.sort_values("american_price",ascending=False)).iloc[0]
                d["close_price"]=float(c.american_price)
                d["clv_probability_points"]=clv_probability_points(float(r.american_price),float(c.american_price))
        out.append(d)
    audited=pd.DataFrame(out)
    if audited.empty: return audited,pd.DataFrame()
    graded=audited[audited.result.isin(["WIN","LOSS","PUSH"])].copy()
    graded["ev_bucket"]=pd.cut(pd.to_numeric(graded.get("EV_CONSERVATIVE"),errors="coerce"),[-1e9,0,2,4,6,10,1e9],labels=["<0","0-2","2-4","4-6","6-10","10+"])
    summary=graded.groupby(["market_family","ev_bucket"],observed=True).agg(
        bets=("result","size"), wins=("result",lambda x:(x=="WIN").sum()), losses=("result",lambda x:(x=="LOSS").sum()),
        pushes=("result",lambda x:(x=="PUSH").sum()), realized_roi=("unit_pnl","mean"), avg_ev_cons=("EV_CONSERVATIVE","mean"),
        avg_clv_pp=("clv_probability_points","mean"), avg_confidence=("confidence","mean")
    ).reset_index()
    return audited,summary


def write_audit(master_path: str | Path, results_path: str | Path, out_dir: str | Path, close_path: str | Path | None = None):
    master=pd.read_csv(master_path); results=pd.read_csv(results_path); close=pd.read_csv(close_path) if close_path else None
    audited,summary=audit_board(master,results,close)
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    audited.to_csv(out/"POST_SLATE_AUDIT.csv",index=False); summary.to_csv(out/"CALIBRATION_SCORECARD.csv",index=False)
    return out
