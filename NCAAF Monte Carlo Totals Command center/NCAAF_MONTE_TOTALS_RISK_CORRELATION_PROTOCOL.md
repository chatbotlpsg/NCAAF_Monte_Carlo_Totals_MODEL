# NCAAF Risk and Correlation Protocol

The Trading Agent must not treat multiple correlated totals positions as independent bets.

Required correlation clusters:

```text
FG_OVER ↔ HOME_TT_OVER
FG_OVER ↔ AWAY_TT_OVER
FG_OVER ↔ H1_OVER
HOME_TT_OVER ↔ H1_OVER
AWAY_TT_OVER ↔ H1_OVER
same_game_total_cluster
same_team_total_cluster
weather_under_cluster
pace_up_cluster
blowout_substitution_cluster
```

Do not stack positions without stating shared risk.

Risk-room grades:

```text
PASS
WATCH
VALUE
ELITE
```

`ELITE` requires positive conservative EV, no hard blocker, strong confidence, fresh price, converged simulation, and acceptable correlation.
