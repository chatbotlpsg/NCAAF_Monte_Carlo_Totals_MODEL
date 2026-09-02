# AITA NCAAF Monte Carlo Totals Desk V1.1 — 2026

This package implements the **Python quantitative side** of the locked NCAAF architecture:

`data -> normalized football state -> possessions/drives -> Monte Carlo -> ALL-GAME FG/team/H1 model boards -> exact market comparison -> provisional EV/confidence/correlation/risk support -> immutable Trading-Agent handoff ZIP`

The dedicated NCAAF Trading Agent is **not embedded here**. Python ends after creating and validating the handoff ZIP.

## V1.1 production contract

1. **Every discovered game is modeled.**
   - ESPN display names are separated from canonical school/model keys.
   - When a team cannot be resolved to a CFBD state (common with sparse FCS opponents), the model uses a **dynamic high-uncertainty sparse prior** instead of deleting the game.
   - The fallback is explicitly labeled; it is never represented as normal-quality CFBD data.
2. **Model boards and EV boards are separate.**
   - `03_FULL_GAME_TOTALS_BOARD.csv`: one row for every modeled game.
   - `04_TEAM_TOTALS_BOARD.csv`: two rows for every modeled game.
   - `05_FIRST_HALF_TOTALS_BOARD.csv`: one row for every modeled game.
   - `02_MASTER_EV_BOARD.csv`: only exact two-sided sportsbook markets. No exact price = no EV row.
3. **EV is explicitly uncalibrated in V1.1.**
   - `calibration_status=UNCALIBRATED`
   - `ev_estimate_status=PROVISIONAL_UNCALIBRATED`
   - Python stake recommendations are disabled until calibration is promoted.
   - EV math remains visible for research/ranking by the external Trading Agent.
4. **Missing weather/QB information does not erase a game.**
   - It lowers confidence / adds warnings.
   - The model-only projection still exists.
5. **Missing Odds API event mapping does not erase a game.**
   - The model board remains available.
   - Market/EV fields stay unavailable rather than being fabricated.
6. **Postgame grading/audit/close capture are NOT Python responsibilities.**
   - The external NCAAF Trading Agent owns close capture, grading, CLV, ROI, slate recap, and audit history.

## Quick validation

```bash
ncaaf-aita doctor
pytest -q
```

Release regression suite: **15 tests**.

## Production example

```bash
ncaaf-aita discover-slate --date 2026-09-03

ncaaf-aita refresh-rosters \
  --season 2026 \
  --slate data/normalized/SLATE_EVENTS.csv

ncaaf-aita build-team-states \
  --year 2026 \
  --week 1

ncaaf-aita run \
  --season 2026 \
  --week 1 \
  --slate-date 2026-09-03 \
  --slate data/normalized/SLATE_EVENTS.csv \
  --team-states data/features/TEAM_STATES.csv \
  --stadiums data/normalized/STADIUMS.csv \
  --live-odds \
  --simulations 250000
```

The resulting `NCAAF_MONTE_TOTALS_..._TRADING_AGENT_HANDOFF_<RUN_ID>.zip` is the formal Python boundary. Feed that ZIP to the external Trading Agent.
