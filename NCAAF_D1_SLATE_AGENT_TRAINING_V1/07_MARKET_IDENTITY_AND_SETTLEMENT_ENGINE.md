# Market Identity and Settlement Engine

Unique market identity:
```text
event + market_family + period + team + point + book + side
```

Changing any field changes the claim.

## Settlement Value
```text
FG_TOTAL        = away_final + home_final
HOME_TEAM_TOTAL = home_final
AWAY_TEAM_TOTAL = away_final
H1_TOTAL        = away_h1 + home_h1
```

## Outcome
For realized `V` and line `L`:
```text
V > L → Over WIN / Under LOSS
V < L → Over LOSS / Under WIN
V = L → PUSH / PUSH
```

## Market Settlements Schema
```text
capture_tier
aita_event_id
matchup
market_family
period
team_if_applicable
entry_book
entry_line
close_line
settlement_value
entry_over_outcome
entry_under_outcome
close_over_outcome
close_under_outcome
settlement_basis
result_source
```

This file settles markets only. CLV, EV, ROI, and calibration remain Trading-Agent tasks.
