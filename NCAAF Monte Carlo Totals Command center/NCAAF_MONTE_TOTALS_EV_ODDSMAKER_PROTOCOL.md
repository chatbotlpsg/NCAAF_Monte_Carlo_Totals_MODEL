# NCAAF Monte Totals EV Odds-Maker Protocol

EV must be calculated against exact sportsbook line and exact price.

For American odds:

```text
negative odds: payout_b = 100 / abs(odds)
positive odds: payout_b = odds / 100
EV_per_dollar = p_true * payout_b - (1 - p_true)
EV_percent = 100 * EV_per_dollar
```

Trading-desk action should prioritize `EV_CONSERVATIVE`, not raw Monte Carlo EV alone.

Required ranking hierarchy:

1. No hard blocker.
2. Positive conservative EV.
3. Adequate probability edge over break-even.
4. Adequate confidence and convergence.
5. Fresh market price.
6. Clean canonical market identity.
7. Correlation/exposure acceptable.
8. Strong edge-driver support.

A row with no exact price has no EV, regardless of model lean.
