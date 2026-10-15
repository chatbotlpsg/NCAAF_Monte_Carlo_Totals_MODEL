# QA and Completion Gates

## Slate Identity
- [ ] correct date/season;
- [ ] correct model handoff;
- [ ] all modeled D1 games included;
- [ ] no prior-slate prices mixed in.

## Results
- [ ] every modeled game attempted;
- [ ] H1 from verified Q1/Q2 or halftime;
- [ ] regulation/final split for OT;
- [ ] status/source/timestamp present.

## Closing Lines
For every populated row:
- [ ] exact book;
- [ ] exact event;
- [ ] exact market/period/team;
- [ ] same point for both sides;
- [ ] Over and Under present;
- [ ] label justified;
- [ ] source named;
- [ ] line movement correct.

## Recovery
- [ ] all T1 gaps retried before T2;
- [ ] full-game book matrix attempted;
- [ ] 1H book matrix attempted;
- [ ] team-total archive attempted;
- [ ] sportsbook identity checked;
- [ ] mixed-book rows rejected;
- [ ] corrupt cells rejected.

## Completion Classes
```text
FULL_CLV_READY    all required closes verified
PARTIAL_CLV_READY results complete; some closes unresolved
RESULTS_ONLY      results complete; close coverage inadequate
BLOCKED           result/event integrity unresolved
```

Never force `FULL_CLV_READY`.
