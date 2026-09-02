import json
import zipfile
from pathlib import Path
import pandas as pd

from ncaaf_aita.config import load_config
from ncaaf_aita.pipeline import run_quant_pipeline


def _state(team):
    return {
        "team":team,"offense_ppd":2.7,"defense_ppd_allowed":2.5,"possessions_mean":12.3,"possessions_sd":1.4,
        "td_share":.69,"fg_share":.22,"turnover_rate":.12,"explosive_rate":.12,"pass_rate":.50,
        "qb_continuity":.60,"roster_continuity":.60,"offense_sigma":.24,"defense_sigma":.24,
        "sample_size":0,"source_quality":.70,"roster_known":False,"qb_known":False,"pbp_known":False,
    }


def test_every_game_gets_model_board_and_ev_can_be_empty(tmp_path):
    cfg=load_config("configs/default.yaml")
    slate=pd.DataFrame([
        {"aita_event_id":"E1","odds_event_id":"","home_team":"Rutgers Scarlet Knights","home_team_model":"Rutgers","away_team":"Massachusetts Minutemen","away_team_model":"Massachusetts","neutral_site":False},
        {"aita_event_id":"E2","odds_event_id":"","home_team":"Missouri Tigers","home_team_model":"Missouri","away_team":"Arkansas-Pine Bluff Golden Lions","away_team_model":"Arkansas-Pine Bluff","neutral_site":False},
    ])
    states=pd.DataFrame([_state("Rutgers"),_state("Massachusetts"),_state("Missouri")])
    z=run_quant_pipeline(cfg=cfg,slate=slate,team_states=states,market=pd.DataFrame(),season=2026,week=1,slate_date="2026-09-03",output_root=tmp_path,simulation_count=5000)
    assert z.exists()
    run_dirs=[p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(run_dirs)==1
    d=run_dirs[0]
    fg=pd.read_csv(d/"03_FULL_GAME_TOTALS_BOARD.csv")
    tt=pd.read_csv(d/"04_TEAM_TOTALS_BOARD.csv")
    h1=pd.read_csv(d/"05_FIRST_HALF_TOTALS_BOARD.csv")
    ev=pd.read_csv(d/"02_MASTER_EV_BOARD.csv")
    assert len(fg)==2
    assert len(tt)==4
    assert len(h1)==2
    assert len(ev)==0
    assert "EV_CONSERVATIVE" in ev.columns
    assert (fg["market_status"]=="MODEL_ONLY_NO_EXACT_MARKET").all()
    assert "SPARSE_PRIOR_MODEL" in set(fg["model_status"])
    manifest=json.loads((d/"00_MANIFEST.json").read_text())
    assert manifest["model_coverage"]["modeled_events"]==2
    assert manifest["calibration_status"]=="UNCALIBRATED"


def test_display_name_resolves_to_model_location(tmp_path):
    cfg=load_config("configs/default.yaml")
    slate=pd.DataFrame([{"aita_event_id":"E1","odds_event_id":"","home_team":"Rutgers Scarlet Knights","away_team":"Akron Zips","neutral_site":False}])
    states=pd.DataFrame([_state("Rutgers"),_state("Akron")])
    z=run_quant_pipeline(cfg=cfg,slate=slate,team_states=states,market=pd.DataFrame(),season=2026,week=1,slate_date="2026-09-03",output_root=tmp_path,simulation_count=5000)
    d=[p for p in tmp_path.iterdir() if p.is_dir()][0]
    fg=pd.read_csv(d/"03_FULL_GAME_TOTALS_BOARD.csv")
    assert fg.iloc[0]["home_team_model"]=="Rutgers"
    assert fg.iloc[0]["away_team_model"]=="Akron"
    assert fg.iloc[0]["model_status"]=="FULL_MODEL"


def test_unsafe_program_prefix_does_not_resolve_to_wrong_fbs_team(tmp_path):
    cfg=load_config("configs/default.yaml")
    slate=pd.DataFrame([{"aita_event_id":"E1","odds_event_id":"","home_team":"Missouri Tigers","home_team_model":"Missouri","away_team":"Arkansas-Pine Bluff Golden Lions","away_team_model":"Arkansas-Pine Bluff","neutral_site":False}])
    states=pd.DataFrame([_state("Missouri"),_state("Arkansas")])
    run_quant_pipeline(cfg=cfg,slate=slate,team_states=states,market=pd.DataFrame(),season=2026,week=1,slate_date="2026-09-03",output_root=tmp_path,simulation_count=3000)
    d=[p for p in tmp_path.iterdir() if p.is_dir()][0]
    fg=pd.read_csv(d/"03_FULL_GAME_TOTALS_BOARD.csv")
    assert fg.iloc[0]["away_team_model"]=="Arkansas-Pine Bluff"
    assert fg.iloc[0]["model_status"]=="SPARSE_PRIOR_MODEL"


def test_longest_mascot_prefix_prefers_georgia_tech_over_georgia(tmp_path):
    cfg=load_config("configs/default.yaml")
    slate=pd.DataFrame([{"aita_event_id":"E1","odds_event_id":"","home_team":"Georgia Tech Yellow Jackets","away_team":"Colorado Buffaloes","neutral_site":False}])
    states=pd.DataFrame([_state("Georgia"),_state("Georgia Tech"),_state("Colorado")])
    run_quant_pipeline(cfg=cfg,slate=slate,team_states=states,market=pd.DataFrame(),season=2026,week=1,slate_date="2026-09-03",output_root=tmp_path,simulation_count=3000)
    d=[p for p in tmp_path.iterdir() if p.is_dir()][0]
    fg=pd.read_csv(d/"03_FULL_GAME_TOTALS_BOARD.csv")
    assert fg.iloc[0]["home_team_model"]=="Georgia Tech"
    assert fg.iloc[0]["model_status"]=="FULL_MODEL"
