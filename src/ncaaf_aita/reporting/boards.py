from __future__ import annotations

from pathlib import Path
import pandas as pd


def render_markdown(master: pd.DataFrame, full_game: pd.DataFrame, team_totals: pd.DataFrame,
                    h1_totals: pd.DataFrame, path: str | Path, metadata: dict):
    p = Path(path); p.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# NCAAF AITA Monte Carlo Totals — Quant Handoff Board",
        "",
        f"- Run ID: `{metadata.get('run_id')}`",
        f"- Season/Week: `{metadata.get('season')}` / `{metadata.get('week')}`",
        f"- Slate: `{metadata.get('slate_date')}`",
        f"- Model: `{metadata.get('model_version')}`",
        f"- Data quality: **{metadata.get('data_quality_status')}**",
        f"- Model coverage: **{(metadata.get('model_coverage') or {}).get('modeled_events', 0)}/{(metadata.get('model_coverage') or {}).get('slate_events', 0)} games**",
        f"- EV calibration: **{metadata.get('calibration_status')}** — `{metadata.get('ev_estimate_status')}`",
        "- Boundary: **Python prices/model-support only; final trading, close capture, grading, CLV/ROI and post-slate audit belong to the external NCAAF Trading Agent.**",
        "",
        "> EV% is a mathematically valid model-implied estimate at the quoted price, but it is explicitly provisional until enough live calibration samples exist. Model-only totals are still produced when an exact sportsbook market is unavailable.",
        "",
    ]

    lines += ["## Full-Game Totals — Every Modeled Game", ""]
    if full_game.empty:
        lines.append("No games were successfully simulated.")
    else:
        cols=[c for c in ["matchup","model_mean_total","model_fair_total","book_total","model_total_edge_points","p_over_book","p_under_book","model_lean","market_status","model_status","simulation_converged"] if c in full_game]
        lines.append(full_game[cols].to_markdown(index=False, floatfmt=".4f"))

    lines += ["", "## Team Totals — Model Board", ""]
    if team_totals.empty:
        lines.append("No team-total model rows were produced.")
    else:
        cols=[c for c in ["team","matchup","model_mean_points","model_fair_team_total","book_team_total","model_team_total_edge_points","p_over_book","p_under_book","model_lean","market_status","model_status"] if c in team_totals]
        lines.append(team_totals[cols].to_markdown(index=False, floatfmt=".4f"))

    lines += ["", "## First-Half Totals — Model Board", ""]
    if h1_totals.empty:
        lines.append("No first-half model rows were produced.")
    else:
        cols=[c for c in ["matchup","model_mean_h1_total","model_fair_h1_total","book_h1_total","model_h1_edge_points","p_over_book","p_under_book","model_lean","market_status","model_status"] if c in h1_totals]
        lines.append(h1_totals[cols].to_markdown(index=False, floatfmt=".4f"))

    lines += ["", "## Master EV Board — Exact-Priced Markets Only", ""]
    if master.empty:
        lines += ["No exact two-sided sportsbook markets qualified for EV calculation. This does **not** suppress the model-only totals boards above."]
    else:
        cols = [c for c in ["quant_rank","matchup","market_family","team_if_applicable","side","point","american_price","bookmaker_title","P_MC","P_BLEND","P_CONSERVATIVE","EV_CONSERVATIVE","confidence","quant_grade","calibration_status","ev_estimate_status"] if c in master.columns]
        lines.append(master[cols].head(80).to_markdown(index=False, floatfmt=".4f"))

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
