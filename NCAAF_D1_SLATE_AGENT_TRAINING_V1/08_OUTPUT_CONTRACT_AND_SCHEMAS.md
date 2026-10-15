# Output Contract and Schemas

## 00_SLATE_IDENTITY.md
Include:
```text
Sport
Division
Season
Slate date
Run ID / handoff ID
Handoff filename
Modeled game count
Target count
T1 count
Books
Markets
Result status
Close status
Coverage limits
Audit readiness
```

## 01_SLATE_EVENTS.csv
```text
aita_event_id,slate_date,kickoff_local,kickoff_utc,away_team,home_team,
away_subdivision,home_subdivision,game_status,model_included,
market_mapping_status,schedule_source
```

## 02_CAPTURE_TARGETS.csv
```text
capture_tier,aita_event_id,matchup,market_family,period,team_if_applicable,
entry_line,entry_book,entry_over_price,entry_under_price,entry_captured_at,
source_handoff_file
```

## 03_RESULTS.csv
Use `04_RESULTS_CAPTURE_PLAYBOOK.md`.

## 04_CLOSING_LINES.csv
Use `05_CLOSING_LINE_CAPTURE_PLAYBOOK.md`.

## 05_MARKET_SETTLEMENTS.csv
Use `07_MARKET_IDENTITY_AND_SETTLEMENT_ENGINE.md`.

## 06_GAP_REGISTER.csv
```text
aita_event_id,market_family,period,team_if_applicable,entry_line,entry_book,
missing_field,reason,sources_attempted,retry_path,status
```

## 07_SOURCE_LEDGER.csv
```text
source,source_type,used_for,market_coverage,book_coverage,timestamp_quality,
reliability_note,rows_supported
```

## 09_CLOSE_RECOVERY_LOG.csv
```text
aita_event_id,market_family,team_if_applicable,entry_line,entry_book,
original_status,recovered_close_line,close_over_price,close_under_price,
close_label,close_source,line_moved,recovery_notes
```
