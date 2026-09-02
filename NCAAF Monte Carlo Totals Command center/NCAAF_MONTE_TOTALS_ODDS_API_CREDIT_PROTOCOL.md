# NCAAF Odds API Credit Discipline Protocol

The Trading Agent reads the usage ledger and flags quota risk. It does not initiate new paid calls from board-printing mode.

V1 policy:

```text
sport key: americanfootball_ncaaf
slate discovery: /events when available
slate-wide market: totals
derivative event markets: team_totals, totals_h1 only after shortlist
```

Never use polling loops. Never query non-V1 markets without explicit project upgrade.

Required ledger fields:

```text
timestamp
endpoint
sport
markets
regions/bookmakers
event_id
cost_last
credits_used
credits_remaining
run_id
```
