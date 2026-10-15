# NCAAF 2026 Week 1 — Results & Closing-Line Capture

Capture status: results=[11/11 complete] | closes=[41/46 targets, 20/24 T1] | true_close=[0] | close_proxy=[66] | data_gap=[5] | sources=[official team athletics box scores, The Football Database, The Odds Gap archive, SportsbookReview archive, ATS.io archived odds] | captured_at=[2026-09-04T20:43:36Z]

## Recovery Update

- Original unresolved book-level rows: **29**
- Total recovered from the original gaps: **24**
- Remaining unresolved book-level rows: **5**
- Fully complete target groups: **41/46**
- Fully complete T1 target groups: **20/24**
- `TRUE_CLOSE` remains **0**; all historical recoveries remain conservatively labeled `CLOSE_PROXY_PUBLIC`.

## Remaining Gap Register

| aita_event_id | Market | Entry Line | Book | Missing Field | Reason | Retry Path |
|---|---|---:|---|---|---|---|
| AITA_2026-09-03_002 | H1_TOTAL | 32.5 | DraftKings | close_line; close_over_price; close_under_price; close_captured_at | SportsbookReview's DraftKings 1H cell is internally corrupt/implausible (26.5 O -416 / U -108). Other sources do not establish the exact DraftKings two-sided close. | Direct DraftKings historical feed/screenshot or a second book-specific archive. |
| AITA_2026-09-03_008 | AWAY_TEAM_TOTAL — Colorado Buffaloes | 21.5 | FanDuel | close_line; close_over_price; close_under_price; close_captured_at | ATS.io shows Colorado 23.5, but its best-price table assigns FanDuel to the Over and BetMGM to the Under. The FanDuel Under price at the same point is not exposed and cannot be inferred. | Direct FanDuel historical feed/screenshot exposing both sides at the same point. |
| AITA_2026-09-03_008 | HOME_TEAM_TOTAL — Georgia Tech Yellow Jackets | 29.5 | FanDuel | close_line; close_over_price; close_under_price; close_captured_at | ATS.io shows Georgia Tech 30.5, but its best-price table assigns FanDuel to the Over and BetMGM to the Under. The FanDuel Under price at the same point is not exposed and cannot be inferred. | Direct FanDuel historical feed/screenshot exposing both sides at the same point. |
| AITA_2026-09-03_011 | AWAY_TEAM_TOTAL — UAB Blazers | 13.5 | FanDuel | close_line; close_over_price; close_under_price; close_captured_at | ATS.io's displayed UAB 13.5 two-sided team-total pair resolves to BetMGM, not FanDuel. Caliente also has a two-sided market, but cross-book substitution is prohibited. | Direct FanDuel historical feed/screenshot exposing both sides at the same point. |
| AITA_2026-09-03_011 | HOME_TEAM_TOTAL — Illinois Fighting Illini | 41.5 | FanDuel | close_line; close_over_price; close_under_price; close_captured_at | ATS.io's displayed Illinois 39.5 two-sided team-total pair resolves to BetMGM, not FanDuel. Other archives do not expose a verified FanDuel two-sided close. | Direct FanDuel historical feed/screenshot exposing both sides at the same point. |

## Source Ledger

| Source | Used For | Reliability Note |
|---|---|---|
| Official school athletics / structured box scores | Results and quarter scoring | Results file unchanged; 11/11 complete. |
| SportsbookReview full-game totals archive | BetRivers FG and other book-specific FG closes | Public historical book matrix; `CLOSE_PROXY_PUBLIC`. |
| SportsbookReview 1H totals archive | BetRivers 1H and other 1H closes | Public historical book matrix; corrupt BCU-UCF DraftKings cell rejected. |
| ATS.io archived odds pages | FanDuel team totals where book identity is explicitly resolved | Used only when both sides at one point are attributable to FanDuel without substitution. |
| The Odds Gap archive | Previously captured FG totals with pre-kick archival timestamps | Public historical aggregator; `CLOSE_PROXY_PUBLIC`. |

## Audit Readiness

Results grading can proceed for all 11 games. Full CLV can proceed for **41/46** target groups including **20/24 T1** groups. The remaining 5 book-level rows remain excluded rather than guessed, interpolated, or cross-book substituted.
