# Full-Game Totals Protocol

Full-game totals are priced from final-score Monte Carlo paths:

```text
TOTAL_s = HOME_POINTS_s + AWAY_POINTS_s
```

The Trading Agent reviews:

- model mean total;
- model median total;
- score percentiles;
- P_OVER / P_UNDER / P_PUSH where applicable;
- market total and price;
- EV_CONSERVATIVE;
- confidence;
- convergence;
- weather and tempo risks;
- correlation with team totals and H1 totals.

Integer totals must preserve push probability where supplied.
