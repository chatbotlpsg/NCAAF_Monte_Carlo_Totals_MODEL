# Results Capture Playbook

## Preferred Results Sources
1. Official school athletics box score.
2. Official conference/NCAA result.
3. Major structured box score.
4. Structured college-football score widget.
5. The Football Database or equivalent historical structured result.

## Required Result Schema
```text
aita_event_id
matchup
away_team
home_team
away_h1_points
home_h1_points
away_reg_points
home_reg_points
away_final_points
home_final_points
went_to_ot
ot_periods
game_status
result_source
result_captured_at
```

## H1 Rule
Read Q1+Q2 or an explicit halftime score. Never backsolve halftime from final scoring.

## OT Rule
- regulation = end of Q4;
- final = official score including OT;
- count OT periods.

## Settlement Basis
- `FG_TOTAL`: official final combined score including OT.
- `HOME_TEAM_TOTAL`: home official final including OT.
- `AWAY_TEAM_TOTAL`: away official final including OT.
- `H1_TOTAL`: combined score through Q2.
