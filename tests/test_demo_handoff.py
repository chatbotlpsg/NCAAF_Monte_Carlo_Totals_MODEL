from pathlib import Path
from ncaaf_aita.cli import _demo_data
from ncaaf_aita.config import load_config
from ncaaf_aita.pipeline import run_quant_pipeline
from ncaaf_aita.handoff.builder import REQUIRED


def test_handoff_contains_contract(tmp_path):
    cfg=load_config("configs/default.yaml")
    s,t,m=_demo_data()
    z=run_quant_pipeline(cfg=cfg,slate=s,team_states=t,market=m,season=2026,week=1,slate_date="2026-09-05",output_root=tmp_path,simulation_count=6000)
    assert z.exists()
    import zipfile
    with zipfile.ZipFile(z) as f:
        names=set(f.namelist())
    assert set(REQUIRED)<=names
