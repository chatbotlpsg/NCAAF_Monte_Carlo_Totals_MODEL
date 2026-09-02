# NCAAF Data Quality and Fail-Closed Protocol

Blocking flags include:

```text
MISSING_ROSTER
MISSING_QB
MISSING_PBP
LOW_SAMPLE
FCS_DATA_SPARSE
WEATHER_UNAVAILABLE
EVENT_MAPPING_FAILED
ODDS_STALE
ODDS_MARKET_MISSING
SIMULATION_NOT_CONVERGED
SCHEMA_DRIFT
```

A blocking flag prevents VALUE/ELITE classification until repaired or explicitly waived in a separate audit note.

Early-season mode must be handled conservatively. Weeks 0-3 should widen uncertainty, shrink model certainty, and avoid false precision unless roster/QB/context quality is strong.
