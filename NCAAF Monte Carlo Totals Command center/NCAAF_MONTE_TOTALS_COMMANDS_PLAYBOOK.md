# NCAAF Monte Totals Commands Playbook

## /print-ncaaf-totals-boards
Default user-facing board renderer for a frozen NCAAF Monte Totals handoff ZIP. Prints source gates, FG totals, team totals, H1 totals, Master EV+ board, Monte Carlo distribution context, edge drivers, risk room, and Odds API usage.

## /qc-ncaaf-handoff
Runs handoff ZIP completeness checks: manifest, required files, hashes, model card, data-quality report, simulation convergence report, market snapshot, and risk board.

## /review-ncaaf-ev-board
Reviews `02_MASTER_EV_BOARD.csv` and ranks candidates by conservative EV after hard blockers.

## /rank-ncaaf-totals-ev
Creates a market-family separated EV ranking for FG_TOTAL, HOME_TEAM_TOTAL, AWAY_TEAM_TOTAL, and H1_TOTAL.

## /validate-ncaaf-slate
Validates ESPN event IDs, odds event IDs, kickoff timestamps, venue/weather resolution, team identity mapping, and slate-date consistency.

## /capture-ncaaf-close-proxy
Reads attached final pre-kick price snapshots and creates close-proxy notes. Does not claim true close unless source evidence supports it.

## /postgame-ncaaf-audit
Reads attached final scores/results plus entry and close-proxy prices; grades EV, CLV, ROI, confidence buckets, market family, and Monte Carlo distribution accuracy.

## /build-ncaaf-recap
Builds the permanent NCAAF slate recap used for future calibration research.
