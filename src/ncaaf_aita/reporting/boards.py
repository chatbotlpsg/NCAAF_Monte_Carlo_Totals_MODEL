from __future__ import annotations

from pathlib import Path
import pandas as pd


def render_markdown(master: pd.DataFrame, path: str | Path, metadata: dict):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# NCAAF AITA Monte Carlo Totals — Quant Handoff Board",
        "",
        f"- Run ID: `{metadata.get('run_id')}`",
        f"- Season/Week: `{metadata.get('season')}` / `{metadata.get('week')}`",
        f"- Slate: `{metadata.get('slate_date')}`",
        f"- Model: `{metadata.get('model_version')}`",
        "- Boundary: **Python pricing/support only; final trade decision belongs to the external NCAAF Trading Agent.**",
        "",
    ]
    if master.empty:
        lines += ["## No priced candidates", "", "No exact two-sided sportsbook markets survived normalization and data-quality gates."]
    else:
        cols = [c for c in ["quant_rank","matchup","market_family","team_if_applicable","side","point","american_price","bookmaker_title","P_MC","P_BLEND","P_CONSERVATIVE","EV_CONSERVATIVE","confidence","quant_grade"] if c in master.columns]
        lines += ["## Master EV Board", "", master[cols].head(40).to_markdown(index=False, floatfmt=".4f")]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
