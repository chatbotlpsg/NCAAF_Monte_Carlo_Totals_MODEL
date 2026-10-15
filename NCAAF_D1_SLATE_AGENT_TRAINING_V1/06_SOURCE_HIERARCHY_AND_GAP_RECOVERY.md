# Source Hierarchy and Gap-Recovery Protocol

The 2026-09-03 run proved that first-pass gaps must be retried by market type.

## Full-Game Totals Recovery
1. Direct sportsbook history/API/screen if available.
2. **SportsbookReview historical full-game totals book matrix.**
3. **The Odds Gap historical event archive**, especially where last-pre-kick timing is exposed.
4. Other book-specific archive meeting the same evidence standard.

## First-Half Totals Recovery
1. Direct sportsbook evidence.
2. **SportsbookReview historical 1H totals book matrix.**
3. Other exact-book, exact-period historical archive.

This recovered the missing BetRivers H1 block on 9/3.

## Team Totals Recovery
1. Direct sportsbook evidence.
2. **ATS.io archived event/team-total pages**, but only when sportsbook identity can be explicitly resolved to the required book.
3. Other exact-book team-total archive.

If Over is FanDuel but Under is BetMGM, that is not a two-sided FanDuel close.

## Source-Consistency Rule
When public archives disagree:
1. prefer a consistent book matrix across the slate;
2. prefer explicit pre-kick timestamp semantics;
3. record the conflict;
4. never average sources.

## Corrupt-Cell Rule
Reject implausible/internally corrupt archive values and preserve them in notes.

Example: the 9/3 BCU–UCF DraftKings H1 archive showed an implausible `26.5 O -416 / U -108`; it remained a gap.

## Recovery Loop
```text
confirm event
→ confirm market/period/team
→ confirm sportsbook
→ search book matrix
→ search event archive
→ verify both sides/same point
→ verify sportsbook identity
→ label conservatively
→ log recovery
→ keep DATA GAP if unresolved
```
