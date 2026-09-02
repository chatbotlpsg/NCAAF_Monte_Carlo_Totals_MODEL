from __future__ import annotations

import numpy as np
import pandas as pd


def _is_pass(play_type: str, text: str) -> bool:
    s = f"{play_type} {text}".lower()
    return any(x in s for x in ("pass", "sack"))


def _is_rush(play_type: str, text: str) -> bool:
    s = f"{play_type} {text}".lower()
    return any(x in s for x in ("rush", "run")) and "pass" not in s


def _is_turnover(play_type: str, text: str) -> bool:
    s = f"{play_type} {text}".lower()
    return any(x in s for x in ("interception", "fumble", "turnover"))


def build_team_states_from_cfbd_plays(plays: list[dict], *, early_season: bool = True) -> pd.DataFrame:
    """Build a versioned football state from CFBD play-by-play.

    The state deliberately keeps both raw PBP features and the compact parameters used by the Monte Carlo engine.
    """
    if not plays:
        return pd.DataFrame()
    df = pd.DataFrame(plays).copy()
    required = {"offense", "defense", "gameId", "driveId", "yardsGained", "playType", "playText", "ppa"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"CFBD plays missing required fields: {sorted(missing)}")
    for c in ("ppa","yardsGained","down","distance","yardsToGoal","period"):
        if c in df: df[c] = pd.to_numeric(df[c], errors="coerce")
    df["yardsGained"] = df["yardsGained"].fillna(0)
    text = (df.playType.fillna("").astype(str) + " " + df.playText.fillna("").astype(str)).str.lower()
    df["pass"] = [_is_pass(a, b) for a, b in zip(df.playType.fillna(""), df.playText.fillna(""))]
    df["rush"] = [_is_rush(a, b) for a, b in zip(df.playType.fillna(""), df.playText.fillna(""))]
    df["turnover"] = [_is_turnover(a, b) for a, b in zip(df.playType.fillna(""), df.playText.fillna(""))]
    df["success"] = df["ppa"].fillna(0) > 0
    df["explosive"] = np.where(df["pass"], df["yardsGained"] >= 20, np.where(df["rush"], df["yardsGained"] >= 12, False))
    df["sack"] = text.str.contains("sack", regex=False)
    df["touchdown"] = text.str.contains("touchdown", regex=False)
    df["field_goal_attempt"] = text.str.contains("field goal", regex=False)
    df["field_goal_good"] = df["field_goal_attempt"] & (text.str.contains("good",regex=False) | text.str.contains("made",regex=False))
    df["safety"] = text.str.contains("safety", regex=False)
    if "yardsToGoal" in df:
        df["red_zone"] = df["yardsToGoal"].fillna(999) <= 20
    else:
        df["red_zone"] = False
    if "down" in df and "distance" in df:
        df["third_down"] = df["down"] == 3
        df["fourth_down"] = df["down"] == 4
        df["conversion_success"] = df["yardsGained"] >= df["distance"].fillna(999)
    else:
        df["third_down"] = False; df["fourth_down"] = False; df["conversion_success"] = False

    # Drive outcomes produce football-shaped scoring parameters instead of relying on final-score Gaussian noise.
    drive_keys=["offense","defense","gameId","driveId"]
    drive=df.groupby(drive_keys,dropna=False).agg(
        td=("touchdown","max"), fg=("field_goal_good","max"), safety=("safety","max"), turnover=("turnover","max"),
        red_zone=("red_zone","max"), plays=("driveId","size"), explosive=("explosive","max"), period_start=("period","min")
    ).reset_index()
    drive["drive_points"] = np.where(drive.td,7,np.where(drive.fg,3,np.where(drive.safety,2,0)))
    drive["rz_td"] = drive["red_zone"] & drive["td"]

    game_poss = drive.groupby(["offense","gameId"])["driveId"].nunique().groupby("offense").agg(["mean","std"]).fillna(1.2)
    h1_poss = drive[drive.period_start.fillna(5)<=2].groupby(["offense","gameId"])["driveId"].nunique().groupby("offense").mean()
    d_off = drive.groupby("offense").agg(
        points_per_drive=("drive_points","mean"), td_drives=("td","sum"), fg_drives=("fg","sum"),
        turnover_drive_rate=("turnover","mean"), scoring_opportunity_rate=("red_zone","mean"),
        red_zone_td_rate=("rz_td","sum"), red_zone_drives=("red_zone","sum")
    )
    d_off["red_zone_td_rate"] = d_off["red_zone_td_rate"] / d_off["red_zone_drives"].replace(0,np.nan)
    d_off["td_share"] = d_off["td_drives"] / (d_off["td_drives"]+d_off["fg_drives"]).replace(0,np.nan)
    d_off["fg_share"] = 1.0-d_off["td_share"]
    d_def = drive.groupby("defense").agg(
        points_per_drive_allowed=("drive_points","mean"), turnover_creation_rate=("turnover","mean"),
        explosive_drive_rate_allowed=("explosive","mean"), rz_td_allowed=("rz_td","sum"), rz_drives_allowed=("red_zone","sum")
    )
    d_def["def_red_zone_td_rate_allowed"] = d_def["rz_td_allowed"] / d_def["rz_drives_allowed"].replace(0,np.nan)

    off = df.groupby("offense").agg(
        off_epa_per_play=("ppa","mean"), success_rate=("success","mean"), explosive_rate=("explosive","mean"),
        pass_rate=("pass","mean"), sample_size=("gameId","nunique"), plays=("gameId","size"),
        sack_rate_allowed=("sack","mean"), third_down_attempt_rate=("third_down","mean"), fourth_down_attempt_rate=("fourth_down","mean"),
    )
    pass_epa=df[df["pass"]].groupby("offense")["ppa"].mean().rename("pass_epa_per_play")
    rush_epa=df[df["rush"]].groupby("offense")["ppa"].mean().rename("rush_epa_per_play")
    third=df[df["third_down"]].groupby("offense")["conversion_success"].mean().rename("third_down_success")
    fourth=df[df["fourth_down"]].groupby("offense")["conversion_success"].mean().rename("fourth_down_success")
    fg=df[df["field_goal_attempt"]].groupby("offense")["field_goal_good"].mean().rename("fg_make_rate")
    deff = df.groupby("defense").agg(
        def_epa_allowed=("ppa","mean"), def_success_rate_allowed=("success","mean"), explosive_rate_allowed=("explosive","mean"),
        sack_rate_created=("sack","mean")
    )

    out = off.join([pass_epa,rush_epa,third,fourth,fg,d_off,d_def,deff,game_poss.rename(columns={"mean":"possessions_mean","std":"possessions_sd"}),h1_poss.rename("first_half_possessions")], how="outer")
    epa_ppd=(2.35 + 1.10*out["off_epa_per_play"].fillna(0)).clip(.8,5.2)
    def_epa_ppd=(2.35 + 1.10*out["def_epa_allowed"].fillna(0)).clip(.8,5.2)
    out["offense_ppd"]=(.70*out["points_per_drive"].fillna(epa_ppd)+.30*epa_ppd).clip(.7,5.5)
    out["defense_ppd_allowed"]=(.70*out["points_per_drive_allowed"].fillna(def_epa_ppd)+.30*def_epa_ppd).clip(.7,5.5)
    out["possessions_mean"] = out["possessions_mean"].fillna(12.2).clip(8.5,17.0)
    out["possessions_sd"] = out["possessions_sd"].fillna(1.35).clip(.7,2.8)
    out["first_half_possessions"] = out["first_half_possessions"].fillna(out["possessions_mean"]/2).clip(3.5,10)
    out["td_share"] = out["td_share"].fillna(.70).clip(.45,.90)
    out["fg_share"] = out["fg_share"].fillna(1-out["td_share"]).clip(.10,.55)
    out["turnover_rate"] = out["turnover_drive_rate"].fillna(.12).clip(.03,.30)
    out["turnover_creation_rate"] = out["turnover_creation_rate"].fillna(.12).clip(.03,.30)
    out["red_zone_td_rate"] = out["red_zone_td_rate"].fillna(.60).clip(.30,.90)
    out["def_red_zone_td_rate_allowed"] = out["def_red_zone_td_rate_allowed"].fillna(.60).clip(.30,.90)
    out["explosive_rate"] = out["explosive_rate"].fillna(.12).clip(.03,.30)
    out["explosive_rate_allowed"] = out["explosive_rate_allowed"].fillna(.12).clip(.03,.30)
    league_fg=float(out["fg_make_rate"].mean()) if out["fg_make_rate"].notna().any() else .75
    out["special_teams_rating"]=(out["fg_make_rate"].fillna(league_fg)-league_fg).clip(-.25,.25)
    out["qb_continuity"] = .50; out["roster_continuity"] = .50
    out["offense_sigma"] = np.where(early_season,.22,.15); out["defense_sigma"] = np.where(early_season,.22,.15)
    out["source_quality"] = np.minimum(.95,.60+.04*out["sample_size"].fillna(0))
    out["fcs_data_sparse"] = False; out["roster_known"] = False; out["qb_known"] = False; out["pbp_known"] = True
    out.index.name="team"
    core_cols=[
        "offense_ppd","defense_ppd_allowed","possessions_mean","possessions_sd","first_half_possessions","td_share","fg_share",
        "turnover_rate","turnover_creation_rate","explosive_rate","explosive_rate_allowed","pass_rate","red_zone_td_rate","def_red_zone_td_rate_allowed",
        "sack_rate_allowed","sack_rate_created","third_down_success","fourth_down_success","pass_epa_per_play","rush_epa_per_play",
        "success_rate","def_success_rate_allowed","points_per_drive","points_per_drive_allowed","scoring_opportunity_rate","fg_make_rate",
        "qb_continuity","roster_continuity","special_teams_rating","offense_sigma","defense_sigma","sample_size","source_quality",
        "fcs_data_sparse","roster_known","qb_known","pbp_known"
    ]
    for col in core_cols:
        if col not in out: out[col]=np.nan
    return out.reset_index()[["team"]+core_cols]

def roster_continuity(current: list[dict], previous: list[dict]) -> dict:
    def ids(rows):
        found = []
        for r in rows:
            athlete = r.get("athlete") if isinstance(r, dict) else None
            rid = (athlete or r).get("id") if isinstance((athlete or r), dict) else None
            if rid is not None: found.append(str(rid))
        return set(found)
    cur, prev = ids(current), ids(previous)
    pct = len(cur & prev) / max(1, len(cur))
    return {"returning_player_pct": pct, "roster_turnover_score": 1.0 - pct}


def enrich_with_core(states: pd.DataFrame, core_rows: list[dict], *, through_week_max: int | None = None) -> pd.DataFrame:
    """Blend CFBD CORE as an opponent-adjusted challenger without replacing raw/PBP features."""
    if states.empty or not core_rows:
        return states
    c = pd.DataFrame(core_rows).copy()
    if c.empty or "team" not in c:
        return states
    if through_week_max is not None and "throughWeek" in c:
        c = c[pd.to_numeric(c["throughWeek"], errors="coerce") <= through_week_max]
    if c.empty:
        return states
    if "throughWeek" in c:
        c = c.sort_values("throughWeek").groupby("team", as_index=False).tail(1)
    keep = [x for x in ["team","overall","offense","defense","offensePlays","defensePlays","modelVersion","throughWeek"] if x in c.columns]
    c = c[keep].rename(columns={
        "overall":"core_overall","offense":"core_offense","defense":"core_defense",
        "offensePlays":"core_offense_plays","defensePlays":"core_defense_plays","modelVersion":"core_model_version","throughWeek":"core_through_week"
    })
    out = states.merge(c, on="team", how="left")
    # Conservative 35% challenger blend in log-space. CORE offense: higher is better; defense: lower is better.
    off_factor = np.exp(pd.to_numeric(out.get("core_offense"), errors="coerce").fillna(0).clip(-35,35)/220.0)
    def_factor = np.exp(pd.to_numeric(out.get("core_defense"), errors="coerce").fillna(0).clip(-35,35)/220.0)
    out["offense_ppd_raw"] = out["offense_ppd"]
    out["defense_ppd_allowed_raw"] = out["defense_ppd_allowed"]
    out["offense_ppd"] = (out["offense_ppd"] * (off_factor ** .35)).clip(.7,5.5)
    out["defense_ppd_allowed"] = (out["defense_ppd_allowed"] * (def_factor ** .35)).clip(.7,5.5)
    out["opponent_adjustment_source"] = np.where(out.get("core_overall").notna(), "CFBD_CORE_CHALLENGER", "NONE")
    return out


def build_preseason_states_from_prior_ratings(core_rows: list[dict], sp_rows: list[dict] | None = None,
                                               elo_rows: list[dict] | None = None) -> pd.DataFrame:
    """Create Week 0/1 priors strictly from prior-season ratings; no current/future results."""
    c = pd.DataFrame(core_rows or []).copy()
    if c.empty or "team" not in c:
        return pd.DataFrame()
    if "throughWeek" in c:
        c = c.sort_values("throughWeek").groupby("team", as_index=False).tail(1)
    rows=[]
    sp = pd.DataFrame(sp_rows or [])
    elo = pd.DataFrame(elo_rows or [])
    sp_map = {str(r.team): r for _,r in sp.iterrows()} if not sp.empty and "team" in sp else {}
    elo_map = {str(r.team): r for _,r in elo.iterrows()} if not elo.empty and "team" in elo else {}
    for _,r in c.iterrows():
        team=str(r.team); co=float(r.get("offense",0) or 0); cd=float(r.get("defense",0) or 0)
        off=float(np.clip(2.35*np.exp(np.clip(co,-40,40)/170.0),.85,4.8))
        deff=float(np.clip(2.35*np.exp(np.clip(cd,-40,40)/170.0),.85,4.8))
        spr=sp_map.get(team); er=elo_map.get(team)
        sp_rating=float(getattr(spr,"rating",0) or 0) if spr is not None else np.nan
        elo_rating=float(getattr(er,"elo",1500) or 1500) if er is not None else np.nan
        # Small challenger adjustments, with uncertainty kept wide until roster/QB continuity is known.
        if np.isfinite(sp_rating): off *= float(np.exp(np.clip(sp_rating,-35,35)/900.0))
        rows.append({
            "team":team,"offense_ppd":float(np.clip(off,.8,5.0)),"defense_ppd_allowed":deff,
            "possessions_mean":12.2,"possessions_sd":1.55,"first_half_possessions":6.1,"td_share":.70,"fg_share":.30,"turnover_rate":.12,"turnover_creation_rate":.12,
            "explosive_rate":.12,"explosive_rate_allowed":.12,"pass_rate":.50,"red_zone_td_rate":.60,"def_red_zone_td_rate_allowed":.60,"sack_rate_allowed":.06,"sack_rate_created":.06,"qb_continuity":.50,"roster_continuity":.50,"special_teams_rating":0.0,
            "offense_sigma":.28,"defense_sigma":.28,"sample_size":0,"source_quality":.67,"fcs_data_sparse":False,
            "roster_known":False,"qb_known":False,"pbp_known":False,"core_overall":r.get("overall"),"core_offense":co,
            "core_defense":cd,"core_model_version":r.get("modelVersion"),"core_through_week":r.get("throughWeek"),
            "sp_rating":sp_rating,"elo_rating":elo_rating,"opponent_adjustment_source":"PRIOR_SEASON_CFBD_CORE_SP_ELO"
        })
    return pd.DataFrame(rows)


def blend_with_preseason_prior(current: pd.DataFrame, prior: pd.DataFrame, *, week: int) -> pd.DataFrame:
    """Early-season shrinkage: blend tiny current samples with previous-season priors."""
    if current.empty: return prior.copy()
    if prior.empty or week > 3: return current.copy()
    c=current.set_index("team"); p=prior.set_index("team")
    teams=sorted(set(c.index)|set(p.index)); rows=[]
    w_cur={1:0.0,2:0.35,3:0.55}.get(int(week),0.70)
    numeric_blend=["offense_ppd","defense_ppd_allowed","possessions_mean","possessions_sd","first_half_possessions","turnover_rate","turnover_creation_rate","explosive_rate","explosive_rate_allowed","pass_rate","red_zone_td_rate","def_red_zone_td_rate_allowed","sack_rate_allowed","sack_rate_created","special_teams_rating"]
    for t in teams:
        if t in c.index: d=c.loc[t].to_dict()
        else: d=p.loc[t].to_dict()
        if t in c.index and t in p.index:
            for col in numeric_blend:
                if col in c.columns and col in p.columns:
                    cv=pd.to_numeric(pd.Series([c.loc[t].get(col)]),errors="coerce").iloc[0]
                    pv=pd.to_numeric(pd.Series([p.loc[t].get(col)]),errors="coerce").iloc[0]
                    if pd.notna(cv) and pd.notna(pv): d[col]=w_cur*float(cv)+(1-w_cur)*float(pv)
            # uncertainty falls only as current evidence accumulates.
            d["offense_sigma"] = max(.18, float(p.loc[t].get("offense_sigma",.28)) - .04*max(0,week-1))
            d["defense_sigma"] = max(.18, float(p.loc[t].get("defense_sigma",.28)) - .04*max(0,week-1))
            d["prior_weight"] = 1-w_cur
        d["team"]=t; rows.append(d)
    return pd.DataFrame(rows)
