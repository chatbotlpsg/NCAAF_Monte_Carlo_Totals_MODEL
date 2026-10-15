# AITA NCAAF Division I Slate Agent — Training Package v1.0

## Purpose
Train the Slate Agent so a user can type only:

```text
9/6 NCAAF D1
```

and receive a standardized NCAAF Division I slate packet covering slate identity, modeled games, target markets, verified results, closing lines, market settlements, gaps, source provenance, and Trading-Agent handoff.

## Required Output Packet
```text
NCAAF_<YYYY-MM-DD>_D1/
├── 00_SLATE_IDENTITY.md
├── 01_SLATE_EVENTS.csv
├── 02_CAPTURE_TARGETS.csv
├── 03_RESULTS.csv
├── 04_CLOSING_LINES.csv
├── 05_MARKET_SETTLEMENTS.csv
├── 06_GAP_REGISTER.csv
├── 07_SOURCE_LEDGER.csv
├── 08_CAPTURE_REPORT.md
├── 09_CLOSE_RECOVERY_LOG.csv
└── 10_POSTGAME_AUDIT_HANDOFF.md
```

## Responsibility Boundary

### Model/Python handoff owns
- frozen probabilities, fair totals, EV%, confidence;
- entry lines/prices and pregame market snapshot;
- target books/markets.

### Slate Agent owns
- event reconciliation;
- final and half-by-half results;
- actual/archived closing-line capture;
- closing provenance and recovery;
- market settlement values;
- gaps and source ledger.

### Trading Agent owns
- CLV;
- grading;
- ROI/P&L;
- EV-vs-close calibration;
- model-performance conclusions.

The Slate Agent is a capture and market-record agent, not a retrospective handicapper.
