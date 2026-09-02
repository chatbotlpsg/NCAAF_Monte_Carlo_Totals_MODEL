# NCAAF Monte Totals Agent Router Patch

Use this routing layer when an attached ZIP/file or user request references:

```text
NCAAF
college football
Monte Carlo totals
full-game totals
team totals
first-half totals
H1 totals
NCAAF_MONTE_TOTALS_*_TRADING_AGENT_HANDOFF.zip
NCAAF_FINAL_BOARDS.md
MASTER_EV_BOARD.csv
FULL_GAME_TOTALS_BOARD.csv
TEAM_TOTALS_BOARD.csv
FIRST_HALF_TOTALS_BOARD.csv
```

## Default route

Route to:

```text
ncaaf-totals-orchestrator-agent
```

Primary command:

```text
/print-ncaaf-totals-boards
```

## Specialist routing

- Handoff ZIP structure / manifest / hash checks → `ncaaf-handoff-intake-agent`
- Data-quality / ESPN / CFBD / weather / schema gaps → `ncaaf-data-quality-agent`
- Odds availability / book prices / market identity / stale prices → `ncaaf-market-price-agent`
- Monte Carlo distribution quality / convergence / halftime-state logic → `ncaaf-monte-distribution-audit-agent`
- Full-game total board → `ncaaf-full-game-totals-agent`
- Team total board → `ncaaf-team-totals-agent`
- First-half total board → `ncaaf-h1-totals-agent`
- EV/fair odds/ranking → `ncaaf-ev-ranking-agent`
- Correlation, exposure, and sizing warnings → `ncaaf-correlation-risk-agent`
- Close-proxy, CLV, ROI, and postgame grading → `ncaaf-close-clv-audit-agent`
- Season recap / calibration feedback → `ncaaf-calibration-recap-agent`
- Missing source / no-fabrication enforcement → `ncaaf-no-fabrication-agent`

## Hard routing rule

Never route this task to generic sports analysis. This project requires NCAAF scoring-distribution, totals-market, and Odds API quota discipline.
