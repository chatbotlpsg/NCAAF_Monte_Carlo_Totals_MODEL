# Team Totals Protocol

Team totals use separate home/away scoring distributions:

```text
HOME_POINTS_s
AWAY_POINTS_s
```

The Trading Agent must check:

- team-specific market identity;
- Over/Under side;
- exact line;
- exact price;
- asymmetric blowout/substitution behavior;
- offense/defense matchup edge drivers;
- correlation with full-game totals;
- correlation with first-half totals.

Do not treat home team total and away team total as interchangeable market rows.
