# NCAAF AITA V1 Implementation Matrix

This release implements the 2026 NCAAF Monte Carlo totals sourcing/build specification and the locked Python-vs-Trading-Agent architecture boundary supplied for the build.

| Requirement | Implementation |
|---|---|
| ESPN operational identity layer | `src/ncaaf_aita/data/espn.py` |
| CFBD advanced/PBP enrichment | `src/ncaaf_aita/data/cfbd.py`, `features/builders.py` |
| Open-Meteo environmental layer | `src/ncaaf_aita/data/weather.py` |
| Odds API cost-aware scanner | `src/ncaaf_aita/data/odds.py`, `cli.py` |
| Immutable raw snapshots | `src/ncaaf_aita/data/cache.py` |
| Canonical entity resolution | `src/ncaaf_aita/data/entities.py` |
| Early-season prior/shrinkage | `features/builders.py`, `pipeline.py` |
| Offense/defense/PBP state | `features/state.py`, `features/builders.py` |
| Tempo/possession distribution | `simulation/engine.py` |
| Sequential drive/game-state MC | `simulation/engine.py` |
| Actual H1 simulation | `simulation/engine.py` |
| FG/team/H1 fair curves | `pricing/curves.py`, `pipeline.py` |
| Vig removal / break-even | `pricing/odds_math.py` |
| P_MC/P_MKT/P_BLEND/P_CONS/P_BE | `ev/engine.py`, `pipeline.py` |
| Push-aware EV | `ev/engine.py` |
| Confidence | `confidence/engine.py` |
| Cross-market correlation | `correlation/engine.py` |
| Risk-support metadata | `risk_support/engine.py` |
| Model-first derivative shortlist | `pipeline.py`, `cli.py` |
| Quota headers/ledger/guards | `data/odds.py` |
| Convergence diagnostics | `pipeline.py` |
| Deterministic handoff ZIP + hashes | `handoff/builder.py` |
| Post-slate audit/calibration hook | `audit/post_slate.py` |
| External Trading Agent remains outside Python | enforced by code layout, manifest and tests |

The Python package intentionally stops at the handoff ZIP. No discretionary NCAAF Trading Agent is embedded in this project.
