# AITA NCAAF Monte Carlo Totals Desk V1 — 2026

This package implements the **Python quantitative side** of the locked NCAAF architecture:

`data -> normalized football state -> possessions/drives -> Monte Carlo -> FG/team/H1 totals pricing -> market comparison -> EV/confidence/correlation/risk support -> immutable Trading-Agent handoff ZIP`

The dedicated NCAAF Trading Agent is **not embedded here**. The Python process ends after creating and validating the handoff ZIP.

## Quick start (Git Bash / Windows)

```bash
cd /c/Python/NCAAF_Monte_Carlo_Totals_MODEL
python -m venv virt
source virt/Scripts/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
cp .env.example .env
python -m ncaaf_aita.cli doctor
pytest -q
python -m ncaaf_aita.cli demo --week 1 --slate-date 2026-09-05
```

The demo is fully offline and validates the simulation/pricing/handoff path without spending API credits.

## Live workflow

1. Put API keys in `.env` or export `ODDS_API_KEY` / `CFBD_API_KEY` in the shell.
2. Build slate identity:

```bash
python -m ncaaf_aita.cli discover-slate --date 2026-09-05
```

3. Build/refresh the team-state feature file from cached CFBD plays or your warehouse:

```bash
python -m ncaaf_aita.cli build-team-states --year 2026 --week 1
```

4. Run the model using a normalized slate and team-state file. The live odds stage is cost-aware and fail-closed.

```bash
python -m ncaaf_aita.cli run \
  --season 2026 \
  --week 1 \
  --slate-date 2026-09-05 \
  --slate data/normalized/SLATE_EVENTS.csv \
  --team-states data/features/TEAM_STATES.csv \
  --live-odds
```

## Non-negotiable invariants

- No sportsbook line enters the pure football simulation.
- Pure MC, market fair, blended and conservative probabilities remain separate.
- Odds are never fabricated.
- Additional Odds API markets are queried only after model shortlisting.
- Entry/close snapshots are timestamped and never overwritten.
- Historical handoffs are immutable.
- No final discretionary trading decision is made by Python.
- There is intentionally no `src/trading_agent/` package.

## Cost-aware market sequence

`--live-odds` enforces the specified two-stage policy:

1. Zero-quota Odds API event identity is used when needed.
2. One slate-wide `totals` pull is made.
3. A **pure Monte Carlo prescreen** runs without sportsbook lines as model inputs.
4. The model compares its finished score distributions to the full-game total only to create a `derivative_interest_score`.
5. Only the top `MAX_DERIVATIVE_EVENTS_PER_RUN` events receive event-level `team_totals,totals_h1` calls.
6. The quota reserve plus weekly/monthly budget guards can block charged calls.

The latest prescreen is written to `data/audits/LATEST_DERIVATIVE_SHORTLIST.csv`.

## Close proxy and post-slate audit

Capture final pre-kick public snapshots only for executed/top-control events:

```bash
python -m ncaaf_aita.cli capture-close \
  --master-board outputs/handoffs/<RUN_ID>/02_MASTER_EV_BOARD.csv \
  --label CLOSE_PROXY_PUBLIC
```

After settlement, create a normalized results CSV with:

```text
aita_event_id,home_team,away_team,final_home_points,final_away_points,h1_home_points,h1_away_points
```

Then audit ROI/CLV/calibration without modifying the original handoff:

```bash
python -m ncaaf_aita.cli audit \
  --master-board outputs/handoffs/<RUN_ID>/02_MASTER_EV_BOARD.csv \
  --results data/audits/results_2026_w01.csv \
  --close-snapshot data/snapshots/close/<TIMESTAMP>_CLOSE_PROXY_PUBLIC.csv \
  --out-dir data/audits/2026_w01
```
