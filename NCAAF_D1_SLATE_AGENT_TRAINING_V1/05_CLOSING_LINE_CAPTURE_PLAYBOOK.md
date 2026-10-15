# Closing-Line Capture Playbook

## Required Closing Schema
```text
capture_tier
aita_event_id
matchup
market_family
period
team_if_applicable
entry_line
entry_book
close_line
close_over_price
close_under_price
close_captured_at
close_label
close_source
line_moved
market_availability
notes
```

## Close Labels
```text
TRUE_CLOSE
CLOSE_PROXY_PUBLIC
FINAL_PRE_KICK_SNAPSHOT
ENTRY
OPEN_PROXY
```

- `TRUE_CLOSE`: direct book evidence that this was the final offer before kickoff.
- `CLOSE_PROXY_PUBLIC`: public archive/aggregator final book-specific price; default historical label.
- `FINAL_PRE_KICK_SNAPSHOT`: specific pre-kick observation not proven to be last.
- `ENTRY`: frozen pregame price only.

## Both-Sides Rule
A valid totals close requires:
```text
same event
same book
same market/period/team
same point
Over price
Under price
```

One side only = `DATA GAP`.

## Line Movement
```text
TRUE  if close_line != entry_line
FALSE if close_line == entry_line
```

Never force the close back to the entry point.

## Market Availability
```text
CLOSED_NORMALLY
MARKET_PULLED_PRE_KICK
MARKET_NOT_OFFERED
UNVERIFIABLE
```
