# Worked Example — 2026-09-03 NCAAF D1

## First Pass
```text
results = 11/11
complete targets = 17/46
T1 complete = 6/24
book-level close proxies = 42
book-level gaps = 29
```

## Recovery Pass
The agent did not stop at 29 gaps.

### BetRivers FG recovered through SportsbookReview book matrix
Examples:
- BCU @ UCF: entry 59.0 → close 58.0, O -112 / U -110.
- Merrimack @ Delaware: 55.0 → 56.5, O -110 / U -113.
- West Georgia @ Kennesaw State: 51.5 → 50.5, O -114 / U -109.
- UAPB @ Missouri: 61.0 → 62.5, O -111 / U -111.
- EIU @ Minnesota: 51.0 → 52.5, O -111 / U -111.
- UAB @ Illinois: 54.5 → 53.5, O -112 / U -110.

### BetRivers H1 recovered through SportsbookReview 1H matrix
- BCU @ UCF: 33.5, -110/-118.
- Akron @ Wake: 27.5, -108/-120.
- Merrimack @ Delaware: 30.5, -119/-109.
- West Georgia @ Kennesaw: 27.5, -104/-123.
- Colorado @ GT: 26.5, -110/-118.
- UAB @ Illinois: 29.5, -115/-112.

### FanDuel team totals recovered through ATS.io where book identity resolved to FanDuel
Examples:
- BCU 6.5, O -148 / U +118.
- UCF 50.5, O -113 / U -113.
- Akron 10.5, O +106 / U -136.
- Wake Forest 38.5, O -104 / U -122.
- UAPB 2.5, O -125 / U -102.
- Missouri 58.5, O -115 / U -111.
- Minnesota 48.5, O -102 / U -125.

## Final Capture State
```text
results = 11/11
complete targets = 41/46
T1 complete = 20/24
book-level close proxies = 66
book-level gaps = 5
TRUE_CLOSE = 0
AUDIT_READINESS = PARTIAL_CLV_READY
```

## Remaining Hard Gaps
- BCU @ UCF DraftKings H1: corrupt archive cell rejected.
- Colorado FanDuel team total: archive split sides across books.
- Georgia Tech FanDuel team total: archive split sides across books.
- UAB FanDuel team total: available two-sided pair resolved to BetMGM.
- Illinois FanDuel team total: exact FanDuel two-sided close not proven.

## Training Lesson
```text
29 gaps
→ identify missing blocks by market/book
→ use book matrices for FG/H1
→ use book-resolved event pages for team totals
→ reduce to genuine provenance gaps
→ stop before fabrication
```
