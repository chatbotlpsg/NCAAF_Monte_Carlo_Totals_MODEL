# NCAAF Monte Totals Agent Orchestrator

## Mission

Coordinate the external NCAAF Trading Agent review after the Python pipeline has emitted the handoff ZIP.

## Agent sequence

1. `ncaaf-handoff-intake-agent` validates manifest, required files, hashes, schema, model card, and ZIP completeness.
2. `ncaaf-data-quality-agent` reviews ESPN/CFBD/weather/source lineage, early-season mode, roster/QB/PBP gaps, and fail-closed flags.
3. `ncaaf-monte-distribution-audit-agent` checks simulation count, convergence, total distribution, team-point distribution, H1 distribution, and model uncertainty.
4. `ncaaf-market-price-agent` confirms canonical market identity, sportsbook, line, price, timestamp, vig-free prior, and stale-price status.
5. Market family specialists review:
   - `ncaaf-full-game-totals-agent`
   - `ncaaf-team-totals-agent`
   - `ncaaf-h1-totals-agent`
6. `ncaaf-ev-ranking-agent` ranks raw/blended/conservative EV and separates PASS/WATCH/VALUE/ELITE candidates.
7. `ncaaf-correlation-risk-agent` checks same-game/team/market-family exposure and duplicate economic positions.
8. `ncaaf-no-fabrication-agent` enforces DATA GAP language for missing evidence.
9. `ncaaf-close-clv-audit-agent` handles close-proxy/result audit only when those files are attached.
10. `ncaaf-calibration-recap-agent` writes permanent post-slate recap and calibration notes.

## Locked principle

Python prices. Trading Agent audits, ranks, risk-filters, and records. Frozen model output remains immutable.
