# NCAAF Monte Carlo Totals — Coding Agent Boundary Prompt

You are implementing the NCAAF Python quant pipeline and Trading-Agent handoff generator.

Do not build the NCAAF Trading Agent inside Python.

Python owns:

```text
data sourcing
normalization
features
possession/drive simulation
Monte Carlo distributions
full-game/team/H1 totals pricing
The Odds API market snapshots
EV/confidence/correlation/risk-support outputs
handoff ZIP generation
```

External Trading Agent owns:

```text
handoff QA
final board interpretation
price availability checks
risk-room judgment
PASS/WATCH/VALUE/ELITE classification
close-proxy capture
postgame CLV/ROI audit
calibration recap
```

Required handoff ZIP files:

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

Acceptance rule:

```text
A production run is complete when the handoff ZIP is generated and validated. Python must stop there.
```
