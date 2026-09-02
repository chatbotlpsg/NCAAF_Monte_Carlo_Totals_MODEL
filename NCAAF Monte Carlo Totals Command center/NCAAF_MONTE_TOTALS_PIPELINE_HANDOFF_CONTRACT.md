# NCAAF Monte Totals Trading-Agent Handoff Contract

The Python pipeline must end by emitting a deterministic ZIP such as:

```text
NCAAF_MONTE_TOTALS_2026_W01_TRADING_AGENT_HANDOFF.zip
```

Required files:

```text
00_MANIFEST.json
01_NCAAF_FINAL_BOARDS.md
02_MASTER_EV_BOARD.csv
03_FULL_GAME_TOTALS_BOARD.csv
04_TEAM_TOTALS_BOARD.csv
05_FIRST_HALF_TOTALS_BOARD.csv
06_GAME_PROJECTIONS.csv
07_MONTE_CARLO_DISTRIBUTIONS.csv
08_MARKET_SNAPSHOT.csv
09_MODEL_CONFIDENCE.csv
10_EDGE_DRIVERS.csv
11_CORRELATION_MATRIX.csv
12_RISK_BOARD.csv
13_DATA_QUALITY_REPORT.json
14_MODEL_CARD.json
15_RUN_AUDIT.json
```

## Required probability fields

Every priced candidate must preserve:

```text
P_MC
P_MARKET_FAIR
P_BLEND
P_CONSERVATIVE
P_BREAK_EVEN
```

The Trading Agent must never overwrite these fields.

## Required EV fields

```text
EV_RAW
EV_BLEND
EV_CONSERVATIVE
fair_price
edge_pp
book
market_line
american_price
snapshot_time
freshness_status
```

## Required diagnostics

```text
simulation_count
convergence_status
model_uncertainty
confidence_score
data_quality_status
hard_flags
edge_drivers
risk_drivers
correlation_cluster
market_family
period
canonical_market_id
```

## Handoff fail conditions

Fail closed if:

```text
manifest missing
required board missing
hash failure
probability outside 0-1
market identity conflict
missing price for EV row
missing timestamp for market snapshot
critical stale data
simulation not converged
blocking data-quality flag
schema drift in critical files
```
