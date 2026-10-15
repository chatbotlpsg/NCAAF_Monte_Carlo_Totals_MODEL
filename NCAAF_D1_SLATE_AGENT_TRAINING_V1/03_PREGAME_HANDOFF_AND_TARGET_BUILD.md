# Pregame Handoff and Capture-Target Build

## Authority Order
1. `00_MANIFEST.json`
2. `01_NCAAF_FINAL_BOARDS.md`
3. Market-specific boards
4. `08_MARKET_SNAPSHOT.csv`
5. `02_MASTER_EV_BOARD.csv`
6. diagnostics as supporting context only

## Canonical Market Families
```text
FG_TOTAL
HOME_TEAM_TOTAL
AWAY_TEAM_TOTAL
H1_TOTAL
```

Normalize generic `TEAM_TOTAL` using team identity.

## One Capture Target per Exact Book Market
```text
capture_tier
aita_event_id
matchup
market_family
period
team_if_applicable
entry_line
entry_book
entry_over_price
entry_under_price
entry_captured_at
source_handoff_file
```

If handoff tiers exist:
- `T1` = official/positive-EV priority set;
- `T2` = control/full-calibration set;
- `T3_BONUS_UNMAPPED` = optional postgame recovery for modeled-but-unmapped games.

The required close must match the **entry sportsbook and market identity**.
