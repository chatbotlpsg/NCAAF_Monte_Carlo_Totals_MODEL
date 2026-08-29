# NCAAF AITA Architecture Boundary Specification
## Python Quant Pipeline vs. External NCAAF Trading Agent

**Status:** LOCKED / NON-NEGOTIABLE  
**Purpose:** Ensure the coding agent preserves the required system boundary between the NCAAF quantitative Python pipeline and the dedicated NCAAF Trading Agent.

---

# 1. Core Architecture Rule

The **NCAAF Trading Agent must remain completely outside the Python modeling pipeline**.

The coding agent is responsible for building:

1. the NCAAF quantitative/data pipeline,
2. the Monte Carlo pricing engine,
3. the EV/confidence/risk outputs,
4. the final Trading-Agent handoff ZIP generator.

The coding agent is **not** responsible for embedding, recreating, or implementing the NCAAF Trading Agent inside Python.

The architecture is:

```text
NCAAF PYTHON PIPELINE
        │
        ├── Source/normalize football data
        ├── Build team/player states
        ├── Build matchup features
        ├── Run possession/drive simulation
        ├── Run Monte Carlo
        ├── Price:
        │     • Full-game totals
        │     • Home team totals
        │     • Away team totals
        │     • 1H totals
        ├── Ingest sportsbook prices
        ├── Calculate fair prices
        ├── Calculate MC / blended / conservative EV%
        ├── Calculate uncertainty/confidence
        ├── Calculate cross-market correlations
        ├── Produce all model and trading-support boards
        │
        ▼
NCAAF TRADING-AGENT HANDOFF ZIP
        │
        ▼
────────────────────────────────────
PYTHON PIPELINE ENDS HERE
────────────────────────────────────
        │
        ▼
SPECIFIC NCAAF TRADING AGENT
        │
        ├── Reads ZIP
        ├── Audits model output
        ├── Reads/ranks EV candidates
        ├── Compares available prices
        ├── Handles correlation/exposure
        ├── Applies trading judgment
        ├── Determines final actionable plays
        ├── Determines PASS / WATCH / VALUE / ELITE
        └── Produces final trading desk
```

---

# 2. Mandate of the Python Pipeline

The Python pipeline's mandate is:

```math
\boxed{\text{PRICE THE MARKET}}
```

It is a deterministic, auditable quantitative engine.

Its responsibilities include:

- sourcing and normalizing NCAAF data,
- building team and player state representations,
- constructing matchup features,
- estimating tempo and possession distributions,
- simulating drives and game states,
- running the Monte Carlo engine,
- producing score distributions,
- pricing the designated NCAAF markets,
- ingesting sportsbook prices,
- calculating break-even probabilities,
- calculating fair odds,
- calculating raw Monte Carlo EV%,
- calculating market-aware/blended EV%,
- calculating conservative EV%,
- quantifying uncertainty,
- generating confidence scores,
- estimating cross-market correlations,
- generating data-quality diagnostics,
- generating risk-support outputs,
- generating machine-readable and human-readable boards,
- packaging all required outputs into the handoff ZIP.

The Python pipeline must **not** make itself responsible for final discretionary trade selection.

---

# 3. Mandate of the NCAAF Trading Agent

The NCAAF Trading Agent's mandate is:

```math
\boxed{\text{TRADE THE MODEL OUTPUT}}
```

The Trading Agent is an external downstream decision system.

It consumes the ZIP produced by the Python pipeline and performs the final trading-layer work.

Its responsibilities include:

- reading the complete handoff,
- auditing model assumptions and diagnostics,
- ranking actionable EV candidates,
- checking whether the quoted market price is still available,
- comparing competing sportsbook prices,
- recognizing correlated exposures,
- applying portfolio-level judgment,
- interpreting confidence and uncertainty,
- incorporating market context,
- determining whether an edge remains actionable,
- classifying plays as:
  - `PASS`
  - `WATCH`
  - `VALUE`
  - `ELITE`
- producing the final NCAAF trading desk,
- making final trade/no-trade recommendations.

The Trading Agent may use the Python outputs, but it must not alter the historical record of what the pure Python model originally produced.

---

# 4. Required Separation of Concerns

The system must preserve a hard boundary between:

## A. Quantitative Pricing

Performed inside Python.

```text
Data
→ Features
→ Simulation
→ Probabilities
→ Fair Prices
→ EV
→ Confidence
→ Correlations
```

## B. Trading Interpretation

Performed by the external NCAAF Trading Agent.

```text
Model Outputs
→ Market Review
→ Portfolio Context
→ Trading Judgment
→ Final Trade / Pass Decision
```

The coding agent must never collapse these two layers into one monolithic Python decision engine.

---

# 5. Required Trading-Agent Handoff ZIP

The Python pipeline must terminate by producing a complete handoff ZIP.

Recommended naming convention:

```text
NCAAF_MONTE_TOTALS_2026_W01_TRADING_AGENT_HANDOFF.zip
```

Required contents:

```text
NCAAF_MONTE_TOTALS_2026_W01_TRADING_AGENT_HANDOFF.zip

├── 00_MANIFEST.json
├── 01_NCAAF_FINAL_BOARDS.md
├── 02_MASTER_EV_BOARD.csv
├── 03_FULL_GAME_TOTALS_BOARD.csv
├── 04_TEAM_TOTALS_BOARD.csv
├── 05_FIRST_HALF_TOTALS_BOARD.csv
├── 06_GAME_PROJECTIONS.csv
├── 07_MONTE_CARLO_DISTRIBUTIONS.csv
├── 08_MARKET_SNAPSHOT.csv
├── 09_MODEL_CONFIDENCE.csv
├── 10_EDGE_DRIVERS.csv
├── 11_CORRELATION_MATRIX.csv
├── 12_RISK_BOARD.csv
├── 13_DATA_QUALITY_REPORT.json
├── 14_MODEL_CARD.json
└── 15_RUN_AUDIT.json
```

The Trading Agent should be able to consume this ZIP without needing direct access to the Python runtime.

---

# 6. Handoff Contract

The handoff ZIP is the formal interface between the two systems.

The Python pipeline must guarantee that every handoff contains:

## Identification

- run ID,
- season,
- week,
- slate date,
- model version,
- build version,
- timestamp,
- environment,
- source snapshots.

## Pricing

- market line,
- sportsbook price,
- break-even probability,
- pure Monte Carlo probability,
- market-implied probability,
- blended probability,
- conservative probability,
- fair odds,
- raw EV%,
- blended EV%,
- conservative EV%.

## Model Diagnostics

- simulation count,
- convergence results,
- model uncertainty,
- confidence score,
- data-quality score,
- source completeness,
- warnings,
- stale-data flags,
- roster/injury uncertainty.

## Football Outputs

- projected home points,
- projected away points,
- projected full-game total,
- projected margin,
- first-half projections,
- score quantiles,
- possession distributions,
- drive/scoring distributions where appropriate.

## Risk Context

- cross-market correlation,
- same-game exposure relationships,
- duplicate-expression flags,
- market conflict flags,
- concentration warnings.

## Explainability

- primary edge drivers,
- primary model risks,
- reasons for confidence reduction,
- reasons for any `PASS` recommendation generated mechanically by the quant layer.

---

# 7. Pure Model Must Remain Preserved

The Python system must preserve the distinction between:

```math
P_{MC}
```

Pure Monte Carlo probability.

```math
P_{MKT}
```

Vig-free market-implied probability.

```math
P_{BLEND}
```

Market-aware blended probability.

```math
P_{CONS}
```

Conservative probability estimate.

```math
P_{BE}
```

Sportsbook break-even probability.

The external Trading Agent may decide which representation deserves the most weight in the final trading decision.

However, the original pure model output must always remain recorded and auditable.

---

# 8. Why This Separation Is Required

This architecture prevents several major failure modes.

## 8.1 Model contamination

If discretionary trading logic is embedded directly into the simulation pipeline, it becomes difficult to distinguish:

- what the football model believed,
- what the market-aware adjustment believed,
- what the Trading Agent ultimately decided.

That destroys clean model attribution.

## 8.2 Backtest contamination

Historical model calibration must evaluate what the quantitative engine actually produced at the time.

The Trading Agent's later interpretation cannot be allowed to rewrite that record.

## 8.3 Auditability

Every final trade should be traceable backward:

```text
Final Trade
    ↓
Trading-Agent Decision
    ↓
Handoff ZIP
    ↓
EV / Confidence / Price
    ↓
Monte Carlo Probability
    ↓
Model Inputs
    ↓
Raw Data Sources
```

## 8.4 Independent improvement

The Python model and Trading Agent can evolve separately.

The quant pipeline may improve:

- possession models,
- drive models,
- team ratings,
- uncertainty,
- calibration,
- Monte Carlo,
- market pricing.

The Trading Agent may separately improve:

- portfolio logic,
- price-shopping logic,
- ranking,
- risk tolerance,
- execution judgment.

Neither system needs to be rewritten simply because the other one changes.

---

# 9. Post-Slate Audit and Calibration Architecture

After games finish, a separate audit/calibration workflow evaluates the system.

The lifecycle becomes:

```math
\boxed{
\text{NCAAF Quant Pipeline}
\rightarrow
\text{Trading-Agent ZIP}
\rightarrow
\text{NCAAF Trading Agent}
}
```

Then after settlement:

```math
\boxed{
\text{Results + Closing Lines}
\rightarrow
\text{Audit/Calibration}
\rightarrow
\text{Next Python Model Version}
}
```

The audit layer should measure:

- actual final score,
- bet result,
- entry price,
- closing price,
- CLV,
- realized ROI,
- raw EV vs realized performance,
- blended EV vs realized performance,
- conservative EV vs realized performance,
- confidence-bucket performance,
- EV-bucket performance,
- market-specific performance,
- correlation/concentration outcomes,
- calibration quality,
- Monte Carlo distribution accuracy.

---

# 10. Calibration Must Feed Back Into Python, Not Retroactively Alter History

The audit process may update future model versions.

Examples:

```text
EV calibration deteriorated
→ increase shrinkage

1H totals outperform full-game totals
→ increase research/capital priority

Team-total overs show weak CLV
→ investigate offensive scoring model

High-uncertainty Week 0 teams are overconfident
→ widen prior distributions

Monte Carlo consistently underprices right-tail scoring
→ improve explosive-play model
```

But prior predictions and handoff ZIPs must remain immutable.

Never overwrite historical output simply because the later model improved.

---

# 11. Recommended Directory Boundary

The implementation should reflect the conceptual separation.

Example:

```text
ncaaf_aita/
│
├── src/
│   ├── data/
│   ├── features/
│   ├── ratings/
│   ├── matchup/
│   ├── possessions/
│   ├── drives/
│   ├── simulation/
│   ├── pricing/
│   ├── ev/
│   ├── confidence/
│   ├── correlation/
│   ├── risk_support/
│   ├── reporting/
│   └── handoff/
│
├── outputs/
│   └── handoffs/
│
├── audits/
├── configs/
├── tests/
└── scripts/
```

There should be **no** package such as:

```text
src/trading_agent/
```

unless it only means serialization/support for the external agent handoff.

It must never contain the actual NCAAF Trading Agent.

---

# 12. Explicit Coding-Agent Prohibitions

The coding agent must **not**:

1. Build the NCAAF Trading Agent inside Python.
2. Let the Trading Agent directly mutate model probabilities.
3. Replace the handoff ZIP with direct in-process communication only.
4. Allow final discretionary trading decisions to overwrite pure model outputs.
5. Hide the pure Monte Carlo probability after blending.
6. Collapse modeling, pricing, and trading into one black-box score.
7. Treat Python-generated rank as automatically equivalent to the final trade decision.
8. Remove historical handoffs after calibration.
9. Backfill future information into prior run outputs.
10. Allow postgame results to modify the historical pregame model record.

---

# 13. Explicit Coding-Agent Requirements

The coding agent **must**:

1. Build the Python quant pipeline independently.
2. Create a stable Trading-Agent handoff schema.
3. Generate the ZIP on every production run.
4. Preserve raw and normalized source snapshots.
5. Preserve pure Monte Carlo outputs.
6. Preserve market-aware outputs separately.
7. Preserve conservative outputs separately.
8. Store all timestamps.
9. Store model and configuration version IDs.
10. Make handoffs reproducible.
11. Make historical handoffs immutable.
12. Provide enough information for the downstream NCAAF Trading Agent to independently audit the model.
13. Provide enough information for post-slate CLV/ROI calibration.
14. Fail closed if required handoff files are missing or corrupted.

---

# 14. Recommended Manifest Fields

`00_MANIFEST.json` should contain at minimum:

```json
{
  "sport": "NCAAF",
  "season": 2026,
  "week": 1,
  "slate_date": "YYYY-MM-DD",
  "run_id": "unique-run-id",
  "model_version": "string",
  "pipeline_version": "string",
  "created_at": "ISO-8601",
  "markets": [
    "full_game_total",
    "home_team_total",
    "away_team_total",
    "first_half_total"
  ],
  "handoff_target": "external_ncaaf_trading_agent",
  "trading_agent_embedded": false,
  "files": [],
  "warnings": [],
  "data_quality_status": "PASS"
}
```

The field:

```json
"trading_agent_embedded": false
```

should effectively remain invariant.

---

# 15. Run Completion Definition

A production pipeline run is complete only when:

```text
Data ingestion
        ✓
Feature generation
        ✓
Monte Carlo
        ✓
Market pricing
        ✓
EV calculations
        ✓
Confidence calculations
        ✓
Correlation analysis
        ✓
Risk-support outputs
        ✓
Boards rendered
        ✓
Manifest generated
        ✓
Audit metadata generated
        ✓
Handoff ZIP validated
        ✓
```

At that point:

```text
PYTHON PIPELINE STATUS = COMPLETE
```

The next system is the external NCAAF Trading Agent.

The Python process must not continue into discretionary trading-agent logic.

---

# 16. Final Locked Architecture

```text
┌───────────────────────────────────────────────┐
│          NCAAF AITA PYTHON QUANT ENGINE       │
│                                               │
│ Data → Features → Ratings → Monte Carlo       │
│      → Fair Prices → EV → Confidence          │
│      → Correlation → Risk Support             │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│       TRADING-AGENT HANDOFF ZIP               │
│                                               │
│ Immutable, Auditable, Reproducible            │
└───────────────────────┬───────────────────────┘
                        │
        PYTHON BOUNDARY │
════════════════════════╪════════════════════════
                        │
                        ▼
┌───────────────────────────────────────────────┐
│        EXTERNAL NCAAF TRADING AGENT           │
│                                               │
│ Audit → Rank → Price Check → Risk Judgment    │
│       → PASS / WATCH / VALUE / ELITE          │
│       → Final Trading Desk                    │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│         POST-SLATE AUDIT / CALIBRATION        │
│                                               │
│ Results → Close → CLV → ROI → Calibration     │
│         → Future Python Model Updates         │
└───────────────────────────────────────────────┘
```

---

# 17. Non-Negotiable Instruction to the Coding Agent

> **Build the NCAAF quantitative Python pipeline and the Trading-Agent ZIP handoff generator. Do not build, embed, or merge the dedicated NCAAF Trading Agent into the Python pipeline. The Python system prices markets; the external NCAAF Trading Agent trades the model output. Preserve this boundary in architecture, code organization, tests, run logic, artifacts, and documentation.**

This architecture is considered locked unless explicitly changed by the project owner.
