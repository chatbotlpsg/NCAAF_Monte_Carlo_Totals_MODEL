# NCAAF Monte Totals Market Protocol

Authorized V1 market families:

```text
FG_TOTAL
HOME_TEAM_TOTAL
AWAY_TEAM_TOTAL
H1_TOTAL
```

Canonical market identity requires:

```text
aita_event_id
market_family
period
team_if_applicable
side
over_under
point
american_price
bookmaker
last_update
snapshot_time
```

Never compare two offers unless the canonical market identity matches exactly.

The Trading Agent must distinguish:

```text
OPEN_PROXY
ENTRY
FINAL_PRE_KICK_SNAPSHOT
CLOSE_PROXY_PUBLIC
TRUE_CLOSE
```

Use `TRUE_CLOSE` only when the source/evidence really supports exact close.
