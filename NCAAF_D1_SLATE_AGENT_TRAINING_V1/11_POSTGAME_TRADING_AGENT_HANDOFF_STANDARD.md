# Postgame Trading-Agent Handoff Standard

Trading Agent read order:
```text
1. 00_SLATE_IDENTITY.md
2. 02_CAPTURE_TARGETS.csv
3. 03_RESULTS.csv
4. 04_CLOSING_LINES.csv
5. 05_MARKET_SETTLEMENTS.csv
6. 06_GAP_REGISTER.csv
7. 08_CAPTURE_REPORT.md
8. 09_CLOSE_RECOVERY_LOG.csv
```

## Full-CLV Eligible Row
Requires:
- final result;
- populated close line;
- both close prices;
- valid source;
- valid close label.

## Results-Only Row
Final result but closing fields remain `DATA GAP`.

## Trading Agent Must Not
- replace gaps with estimates;
- switch books silently;
- treat `CLOSE_PROXY_PUBLIC` as `TRUE_CLOSE`;
- overwrite source provenance.

The Slate Agent must emit:
```text
AUDIT_READINESS=FULL_CLV_READY
AUDIT_READINESS=PARTIAL_CLV_READY
AUDIT_READINESS=RESULTS_ONLY
AUDIT_READINESS=BLOCKED
```
