# One-Line Command Router

## Accepted Command
```text
<DATE> NCAAF D1
```

Examples:
```text
9/6 NCAAF D1
09/06 NCAAF D1
2026-09-06 NCAAF D1
```

Normalize to:
```text
SPORT=NCAAF
DIVISION=I
SLATE_DATE=YYYY-MM-DD
ACTION=BUILD_STANDARD_SLATE_CAPTURE_PACKET
```

## Automatic Workflow
1. Resolve date/season.
2. Locate the authoritative NCAAF Monte Totals handoff if supplied.
3. Read the handoff manifest/boards before using external market information.
4. Build the modeled Division I event set, including FCS opponents in modeled D1 games.
5. Build exact book/market/point capture targets.
6. Check each game's status.
7. Capture verified result and H1 data.
8. Capture/recover closes.
9. Settle every target market.
10. Run QA.
11. Emit the full packet and audit-readiness state.

If games are not final, create the packet with `PENDING_GAME_FINAL` / `PENDING_CLOSE_CAPTURE`; never invent finals.

## Expected Handoff Files
Common NCAAF Monte Totals files:
```text
00_MANIFEST.json
01_NCAAF_FINAL_BOARDS.md
02_MASTER_EV_BOARD.csv
03_FULL_GAME_TOTALS_BOARD.csv
04_TEAM_TOTALS_BOARD.csv
05_FIRST_HALF_TOTALS_BOARD.csv
08_MARKET_SNAPSHOT.csv
09_MODEL_CONFIDENCE.csv
14_MODEL_CARD.json
15_RUN_AUDIT.json
18_FAIR_PRICE_CURVES.csv
```

Use files actually present; do not require optional files.
