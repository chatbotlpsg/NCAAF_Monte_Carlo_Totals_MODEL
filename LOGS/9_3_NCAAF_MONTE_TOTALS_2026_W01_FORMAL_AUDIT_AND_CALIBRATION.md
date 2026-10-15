# NCAAF MONTE CARLO TOTALS — FORMAL AUDIT & CALIBRATION REPORT
## Run `NCAAF_2026_W01_d20e9fbf30` · Slate 2026-09-03 · Model `ncaaf_mc_totals_v1.1.0`

| Field | Value |
|---|---|
| Report type | Formal postgame audit + calibration + board-improvement specification |
| Audit date | 2026-09-05 |
| Trading Agent | AITA NCAAF Monte Carlo Totals Command Center |
| Handoff integrity | 18/18 files present · 18/18 sha256 and byte counts verified · frozen values unmodified |
| Results source | Supplied results file, 11/11 games FINAL, 0 OT, halftime scores present |
| Close source | Supplied capture file, 80 rows, 75 `CLOSE_PROXY_PUBLIC`, 0 `TRUE_CLOSE`, 5 `UNVERIFIABLE` |
| CLV coverage | 132/142 candidates (28 exact-line, 104 ladder-translated), 10 `CLOSE_DATA_GAP` |
| Execution status | `PAPER_ONLY / RISK_ROOM_REVIEW` — no capital was ever at risk |
| Calibration status entering audit | `UNCALIBRATED` / `PROVISIONAL_UNCALIBRATED` |
| **Calibration status exiting audit** | **`FAILED — DO NOT PROMOTE`** |

**On sourcing additional closes:** not required. The supplied capture covers 132 of 142 candidates. The ten unfilled rows (2 Colorado/GT team totals, 2 UAB/Illinois team totals, 1 BCU H1) cannot move the verdict, because the verdict rests on settlement accuracy and probability scoring rather than on CLV. The CLV layer is reported for completeness and is explicitly down-weighted below for the methodological reason given in §3.4.

---

# 1. THE CASINO-QUANT SCORE

> **Question posed:** *Did high-ranked model edge consistently beat the close, price correctly, and outperform lower-ranked edge across the given slate?*

## 1.1 Verdict

| # | Test | Result | Verdict |
|---|---|---|---|
| 1 | Did high-ranked edge **beat the close**? | 49.2% beat-rate across 132 rows (p = 0.931); 46.4% on the 28 methodologically clean rows (p = 0.851) | **NO** |
| 2 | Did the model **price correctly**? | Brier 0.3056 on raw `P_MC` versus 0.2500 for a coin flip and 0.2466 for the market; Brier Skill Score **−0.0358** against the market benchmark | **NO** |
| 3 | Did high-ranked edge **outperform low-ranked edge**? | Spearman ρ(EV rank, outcome) = **−0.294, p = 0.0004**. Rank ordering is significantly **inverted** | **NO — INVERTED** |

**Composite score: 0 / 3. The model failed every leg of the test, and failed leg 3 with statistical significance in the wrong direction.**

This is not a model with a small or unproven edge. It is a model whose ranking key carries real information with the sign reversed on this slate.

## 1.2 The single decisive number

```text
Positive conservative-EV candidates:  28
Wins:                                  7  (25.0%)
Break-even win rate required:             51.5%
Binomial test against required rate:   p = 0.0070
```

A 25% hit rate against a 51.5% requirement, over 28 trials, at p = 0.007. At n = 28 that is a small sample for a subtle effect and an ample sample for an effect this large.

---

# 2. TEST 1 — DID HIGH-RANKED EDGE BEAT THE CLOSE?

## 2.1 Beat-the-close rates

| Cohort | Beat close | Rate | Binomial p vs 50% |
|---|---|---:|---:|
| All rows with a close | 65 / 132 | 49.2% | 0.931 |
| Positive-EV set | 15 / 24 | 62.5% | 0.307 |
| **Exact-line rows only (clean measurement)** | **13 / 28** | **46.4%** | **0.851** |

## 2.2 CLV by EV quintile

| Quintile | n | Mean EV_CONS | Mean CLV pp | Beat close | Mean line CLV (pts) |
|---|---:|---:|---:|---:|---:|
| Q1 (worst EV) | 29 | −13.80% | −0.61 | 40.0% | −0.42 |
| Q2 | 28 | −7.29% | −1.43 | 25.9% | +0.61 |
| Q3 | 28 | −4.81% | +0.01 | 48.1% | +0.07 |
| Q4 | 28 | −1.90% | +1.31 | 71.4% | −0.71 |
| Q5 (best EV) | 29 | +4.01% | +0.67 | 60.0% | +0.48 |

Spearman ρ(EV_CONSERVATIVE, CLV pp) = **+0.212, p = 0.015**.

## 2.3 Why this nominally positive result does not count

Three reasons, all disqualifying:

1. **The overall beat-rate is 49.2%.** A ranking key with genuine market-anticipation content produces a beat-rate meaningfully above 50% somewhere in the distribution. This one does not.
2. **The clean subset says 46.4%.** Of 132 CLV measurements, only 28 compare a like-for-like line. Those 28 beat the close less than half the time.
3. **The other 104 were translated using the model's own broken ladder.** See §3.4. The ρ = +0.212 is measured largely on numbers the failed model generated about itself.

**Leg 1 verdict: FAIL.** No reliable evidence the ranking key anticipated market movement.

---

# 3. TEST 2 — DID THE MODEL PRICE CORRECTLY?

## 3.1 Probability scoring, all 142 priced candidates

| Probability family | Brier ↓ | Log loss ↓ | Mean p | Realized | ρ(p, outcome) |
|---|---:|---:|---:|---:|---:|
| `P_MC` (raw Monte Carlo) | **0.3056** | 0.8155 | 0.5000 | 0.5000 | **−0.312** |
| `P_BLEND` | 0.2663 | 0.7254 | 0.5000 | 0.5000 | −0.306 |
| `P_CONSERVATIVE` | 0.2554 | 0.7039 | 0.5000 | 0.5000 | −0.299 |
| *Coin flip (0.500)* | *0.2500* | *0.6931* | *0.5000* | *0.5000* | *n/a* |
| **`P_MARKET_FAIR` (market)** | **0.2466** | **0.6862** | 0.5000 | 0.5000 | **+0.166** |
| `P_BREAK_EVEN` (vigged market) | 0.2471 | 0.6872 | 0.5258 | 0.5000 | +0.151 |

```text
Brier Skill Score, model vs market benchmark:  -0.0358   (negative = worse than market)
```

Three findings sit in this table:

- **The raw Monte Carlo output scores worse than a coin flip.** Brier 0.3056 against 0.2500. Confident wrong answers are worse than no answer.
- **The market scored better than the model on every metric.** The pipeline's stated purpose is to beat this benchmark.
- **The shrinkage stack is doing real work, and the work it is doing is damage limitation.** `P_MC` 0.3056 → `P_BLEND` 0.2663 → `P_CONSERVATIVE` 0.2554. Each step improves the score by moving the model closer to the market. The conservative layer is not refining an edge; it is diluting an error.

## 3.2 Calibration — `P_MC` (raw model)

| `P_MC` bin | n | Predicted | Realized | Gap (pp) |
|---|---:|---:|---:|---:|
| 0.00 – 0.40 | 24 | 0.249 | 0.750 | **+50.1** |
| 0.40 – 0.50 | 47 | 0.453 | 0.532 | +7.9 |
| 0.50 – 0.60 | 47 | 0.547 | 0.468 | −7.9 |
| 0.60 – 0.70 | 10 | 0.646 | **0.000** | **−64.6** |
| 0.70 – 0.80 | 6 | 0.747 | 0.167 | **−58.1** |
| 0.80 – 0.90 | 5 | 0.846 | 0.400 | −44.6 |
| 0.90 – 1.00 | 3 | 0.947 | 1.000 | +5.3 |

The curve is monotonically wrong through the middle and the upper-middle. Everything the model assigned 60–70% went **0 for 10**. Everything it assigned below 40% went 18 for 24.

## 3.3 Calibration — `P_MARKET_FAIR` (benchmark)

| Bin | n | Predicted | Realized | Gap (pp) |
|---|---:|---:|---:|---:|
| 0.00 – 0.45 | 5 | 0.431 | 0.400 | −3.1 |
| 0.45 – 0.48 | 7 | 0.472 | 0.286 | −18.7 |
| 0.48 – 0.50 | 71 | 0.495 | 0.451 | −4.4 |
| 0.50 – 0.52 | 47 | 0.507 | 0.575 | +6.7 |
| 0.52 – 0.55 | 7 | 0.528 | 0.714 | +18.7 |
| 0.55 – 1.00 | 5 | 0.569 | 0.600 | +3.1 |

Correctly ordered, gaps in single digits across the populated bins. This is what a functioning probability looks like at n = 142.

## 3.4 Methodological disclosure on the CLV layer

104 of the 132 CLV measurements required translating a moved line back to the entry point. That translation used `18_FAIR_PRICE_CURVES.csv` — the model's own ladder. §5 establishes that the model's latent sigma is roughly 1.6× too wide, which makes its ladder too flat and causes it to **understate** the probability change per point of line movement. Ladder-translated CLV is therefore directionally usable and quantitatively soft. This is disclosed rather than buried, and the clean 28-row subset is reported alongside it throughout.

| Method | n | Mean CLV pp | Beat close | ROI |
|---|---:|---:|---:|---:|
| `CLV_EXACT` | 7 (pos-EV) | +1.13 | 86% | −14.2% |
| `CLV_LADDER_ADJ` | 17 (pos-EV) | +0.53 | 53% | −66.7% |
| `CLV_LADDER_ADJ` less the BCU +14.04 outlier | 16 | **−0.32** | — | — |

**Leg 2 verdict: FAIL.** The model priced worse than a coin flip on raw output and worse than the market at every layer.

---

# 4. TEST 3 — DID HIGH-RANKED EDGE OUTPERFORM LOW-RANKED EDGE?

## 4.1 EV_CONSERVATIVE quintiles

| Quintile | n | Mean EV | Hit rate | ROI |
|---|---:|---:|---:|---:|
| **Q1 (worst EV, −13.80%)** | 29 | −13.80% | **0.759** | **+40.70%** |
| Q2 | 28 | −7.29% | 0.571 | +8.37% |
| Q3 | 28 | −4.81% | 0.464 | −12.54% |
| Q4 | 28 | −1.90% | 0.464 | −10.51% |
| **Q5 (best EV, +4.01%)** | 29 | +4.01% | **0.241** | **−53.29%** |

Perfectly monotonic and running backwards from Q1 to Q5.

## 4.2 Decile detail

| Decile | n | Mean EV | Hit | ROI | Mean CLV pp |
|---|---:|---:|---:|---:|---:|
| D1 (highest EV) | 15 | +6.91% | 0.40 | −21.06% | +0.66 |
| D2 | 14 | +0.90% | **0.07** | **−87.83%** | +0.70 |
| D3 | 14 | −1.22% | 0.43 | −17.32% | +2.06 |
| D4 | 14 | −2.59% | 0.50 | −3.69% | +0.56 |
| D5 | 14 | −4.25% | 0.64 | +23.54% | +0.46 |
| D6 | 14 | −5.37% | 0.29 | −48.62% | −0.47 |
| D7 | 14 | −6.56% | 0.50 | −4.80% | −1.10 |
| D8 | 14 | −8.01% | 0.64 | +21.53% | −1.73 |
| D9 | 14 | −10.74% | **1.00** | **+87.18%** | −0.88 |
| D10 (lowest EV) | 15 | −16.66% | 0.53 | −2.69% | −0.39 |

D2 went 1 for 14. D9 went 14 for 14.

## 4.3 Top-N versus Bottom-N

| Cut | Top-N hit | Top-N ROI | Bottom-N hit | Bottom-N ROI |
|---|---:|---:|---:|---:|
| N = 10 | 0.500 | −0.29% | 0.600 | +8.92% |
| N = 20 | 0.300 | −40.80% | 0.650 | +19.88% |
| **N = 28** | **0.250** | **−51.63%** | **0.750** | **+38.90%** |
| N = 50 | 0.340 | −34.28% | 0.680 | +27.03% |

The spread widens as the cut tightens. That is the signature of a ranking key that is working — pointed the wrong way.

## 4.4 Rank-integrity statistics

```text
Spearman  EV_CONSERVATIVE  vs  outcome   rho = -0.294   p = 0.0004
Spearman  EV_CONSERVATIVE  vs  P/L       rho = -0.163   p = 0.0528
Spearman  edge_pp          vs  outcome   rho = -0.296
Spearman  P_MC             vs  outcome   rho = -0.312
Spearman  confidence       vs  outcome   rho = +0.000   p = 1.000
Spearman  confidence       vs  CLV_pp    rho = +0.000   p = 1.000
Spearman  model-vs-market disagreement vs outcome  rho = -0.004
```

## 4.5 Confidence quintiles — the score is inert

| Quintile | n | Mean confidence | Hit rate | ROI | Mean CLV pp |
|---|---:|---:|---:|---:|---:|
| C1 (lowest) | 29 | 52.76 | 0.483 | −12.70% | −0.00 |
| C2 | 28 | 55.92 | 0.536 | +3.69% | −0.03 |
| C3 | 28 | 59.07 | 0.500 | −4.20% | +0.17 |
| C4 | 28 | 62.58 | 0.500 | −5.19% | −0.05 |
| C5 (highest) | 29 | 65.39 | 0.483 | −8.57% | −0.07 |

ρ = 0.000 against outcome and 0.000 against CLV. Not weak — **inert**. Consistent with its construction: `component_sample_size` was pinned at 0.00 and `roster_continuity` at 0.000 on all 142 rows, so the score was measuring the absence of data rather than the quality of an edge. The V1.1 prompt makes confidence the primary ranking key for every board. On this slate that key had no content.

## 4.6 Disagreement size did not predict anything either

| Quintile | n | Mean disagreement | Hit | ROI |
|---|---:|---:|---:|---:|
| D1 (smallest) | 32 | 1.51 pp | 0.500 | −4.89% |
| D2 | 25 | 3.80 pp | 0.520 | −0.50% |
| D3 | 29 | 7.93 pp | 0.483 | −8.29% |
| D4 | 28 | 14.47 pp | 0.500 | −4.24% |
| D5 (largest) | 28 | 32.22 pp | 0.500 | −8.87% |

A 32-point-probability disagreement with the market performed exactly like a 1.5-point disagreement. Disagreement magnitude was pure noise.

**Leg 3 verdict: FAIL — INVERTED, statistically significant.**

---

# 5. ROOT-CAUSE EVIDENCE

## 5.1 `MODEL_DISTRIBUTION_ANOMALY` — CONFIRMED

```text
Model team means:    26.15  →  30.44     SD  1.28
Book team totals:      2.5  →  56.5      SD 18.1
Actual team points:      0  →  73        SD 21.1
```

| Mean absolute error, 16 sides with both a book line and a result | Value |
|---|---:|
| Model | **18.83 pts** |
| Book | **7.69 pts** |

The market was **2.4× more accurate** than the model on the exact markets where the model claimed edges up to +43.70 probability points.

Supporting evidence:

- `mean_possessions` was constant at ~12.20 per side across all 11 games. No tempo model exists.
- `p_home_win` spanned 0.487–0.541 across all 11 games. Actual mean absolute margin was **32.27 points**; games finished by 67, 52, 52, 47, 40 and 35.
- Model `mean_margin` never exceeded 3.24 on any game.

## 5.2 FCS road sides — the pregame natural experiment

| Team | Model | Book | Actual | Model error | Book error |
|---|---:|---:|---:|---:|---:|
| Bethune-Cookman | 27.02 | 7.5 | 6 | **−21.02** | −1.5 |
| Merrimack | 27.75 | 13.5 | 7 | **−20.75** | −6.5 |
| West Georgia | 27.46 | 14.5 | **0** | **−27.46** | −14.5 |
| UAlbany | 27.11 | — | 17 | −10.11 | — |
| Arkansas-Pine Bluff | 26.15 | 2.5 | 14 | −12.15 | +11.5 |
| Eastern Illinois | 27.26 | 2.5 | 7 | **−20.26** | +4.5 |
| Idaho | 26.70 | — | 14 | −12.70 | — |

Model mean for FCS sides **27.06**. Actual mean **9.29**. West Georgia was shut out; the model had them at 27.46.

## 5.3 `H1_FULL_GAME_INCONSISTENCY` — CONFIRMED

```text
Model H1/FG ratio:    0.5047 – 0.5060     SD 0.0004
Actual H1/FG ratio:   0.429  – 0.851      SD 0.1140
```

Actual first-half share varied **285× more** than the model permitted. West Georgia @ Kennesaw put 40 of 47 points in the first half (0.851); the model said 0.506 for that game, as it did for all eleven.

## 5.4 Distribution width

| Metric | Value |
|---|---:|
| FG model MAE (priced games) | 12.76 pts |
| FG **book** MAE (same games) | **11.50 pts** |
| H1 model MAE (priced) | 9.42 pts |
| H1 **book** MAE (same) | **8.00 pts** |
| Actual totals inside model P10–P90 | 10 / 11 |
| Mean P10–P90 width | **67 points** |
| Actual total SD | 16.47 |
| Model implied SD | ~26 |

The 10/11 interval coverage is not a pass. A 24-to-91 band captures nearly anything. Coverage achieved by being uninformative is not calibration, and the over-wide sigma is precisely what pushed deep-tail team-total probabilities to 0.96 and manufactured the largest phantom edges on the board.

## 5.5 Three unmapped games, retro-graded

| Game | Model | Close | Actual | Model err | Close err |
|---|---:|---:|---:|---:|---:|
| UMass @ Rutgers | 57.70 | 54.50 | 58 | **+0.30** | +3.50 |
| UAlbany @ Buffalo | 54.48 | 47.50 | 38 | −16.48 | −9.50 |
| Idaho @ Utah | 56.63 | 60.83 | 80 | +23.37 | +19.17 |

Model beat the close on 1 of 3. The T3 bonus capture recovered three games the mapper lost and does not change the verdict.

---

# 6. SETTLEMENT LEDGER

| Cohort | n | W | L | Push | Units | ROI |
|---|---:|---:|---:|---:|---:|---:|
| All priced candidates | 142 | 71 | 71 | 0 | −7.76 | −5.47% |
| **Positive conservative-EV** | 28 | 7 | 21 | 0 | −14.46 | **−51.63%** |
| Positive-EV, deduplicated | 24 | 6 | 18 | 0 | −12.61 | −52.52% |
| **Negative-EV control** | 114 | 64 | 50 | 0 | +6.69 | **+5.87%** |

| Family | All n | ROI | Pos-EV n | Pos-EV W–L | Pos-EV ROI |
|---|---:|---:|---:|---|---:|
| FG_TOTAL | 62 | −4.52% | 5 | **0–5** | **−100.00%** |
| TEAM_TOTAL | 32 | −8.16% | 14 | 5–9 | −33.97% |
| H1_TOTAL | 48 | −4.89% | 9 | 2–7 | −52.22% |

Mean entry vig across the slate: **5.15%** (range 4.05%–6.54%). Five positive-EV rows carried an edge smaller than the vig they were paying.

---

# 7. DESK DECISION REVIEW

| Pregame call | Outcome |
|---|---|
| 0 rows graded VALUE or ELITE | **Correct.** Would have lost 51.63% of staked capital. |
| `MODEL_DISTRIBUTION_ANOMALY` raised BLOCKING | **Confirmed.** Model MAE 18.83 vs book 7.69. |
| `H1_FULL_GAME_INCONSISTENCY` raised BLOCKING | **Confirmed.** Actual ratio SD 0.114 vs model 0.0004. |
| `TEAM_TOTAL_INCONSISTENCY` raised on 7 FBS-vs-FCS games | **Confirmed.** FCS sides overstated by 10–27 points each. |
| 2 rows graded WATCH (Colorado FG O51.5, H1 O26.5) | Both **lost**. Correct that neither reached VALUE. |
| Real-money authorization withheld | **Correct.** |
| Escalated to Python owner, not patched inline | **Correct.** Boundary held; no frozen value altered pregame or in audit. |

All four desk-raised blocking flags were independently vindicated by the results. Fail-closed was the right posture and it worked.

---

# 8. BOARD IMPROVEMENT SPECIFICATION FOR THE PYTHON PIPELINE

Ordered by priority. Items 1–4 are prerequisites for any future promotion toward calibration.

## 8.1 Model fixes — blocking

| # | Fix | Evidence | Acceptance criterion |
|---|---|---|---|
| M1 | **Add opponent adjustment to team scoring.** Team scoring distributions are currently opponent-independent. | Model team-total MAE 18.83 vs book 7.69 | Team-total MAE ≤ book MAE on a held-out slate |
| M2 | **Add a division-tier term to `DYNAMIC_SPARSE_PRIOR`.** It currently regresses FCS teams to an FBS-average scoring rate. | 7 FCS sides: model mean 27.06, actual mean 9.29 | FCS side mean within 5 pts of realized on a held-out slate |
| M3 | **Derive first-half state from the possession sequence.** H1 is currently a deterministic 0.505 × FG. | Model ratio SD 0.0004 vs actual 0.1140 | H1/FG ratio SD ≥ 0.05 across a slate, or drop the H1 market |
| M4 | **Re-scale latent sigma; it is ~1.6× too wide.** | Implied SD ~26 vs realized 16.47 | P10–P90 width ≤ 40 pts with ≥ 80% empirical coverage |
| M5 | **Build a tempo model.** Possessions are a constant. | `mean_possessions` 12.19–12.20 on all 11 games | Possession SD > 0.5 across a slate |
| M6 | **Fix the odds event mapper.** | 3 of 11 games failed name matching on data already paid for | ≥ 95% mapping rate |

## 8.2 New required handoff fields

Add to the handoff contract:

```text
opponent_adjustment_applied      bool     per team-total row
division_tier_home               enum     FBS_P4 | FBS_G5 | FCS | OTHER
division_tier_away               enum     FBS_P4 | FBS_G5 | FCS | OTHER
cross_division_flag              bool     true when tiers differ
h1_derivation_method             enum     SEQUENTIAL_HALFTIME_STATE | RATIO_APPROXIMATION
h1_fg_ratio                      float    per game, emitted explicitly
blowout_substitution_modeled     bool     currently absent entirely
implied_total_sd                 float    per game
mean_possessions_sd_slate        float    per run
kickoff_utc                      ISO8601  absent from all 18 files
model_vs_book_mae_backtest       float    per market family, rolling
```

## 8.3 New fail-closed gates — Python must refuse to emit

Add to the handoff fail conditions:

```text
H1_RATIO_DEGENERATE          slate SD of h1_fg_ratio < 0.02
TEAM_SCORING_DEGENERATE      slate SD of model team means < 5.0 points
POSSESSION_DEGENERATE        slate SD of mean_possessions < 0.25
SIGMA_OUT_OF_BAND            implied total SD outside 11-20
MARGIN_DEGENERATE            slate SD of mean_margin < 5.0 points
CROSS_DIVISION_UNADJUSTED    cross_division_flag true and opponent_adjustment_applied false
CONFIDENCE_COMPONENT_NULL    any confidence component pinned at 0.00 across all rows
```

Every one of these would have fired on this run. None existed, so a structurally broken model emitted a clean-looking board with 0 blocking flags.

## 8.4 Board changes

**Board 1 / 2 / 3 — add columns:**

| Column | Purpose |
|---|---|
| `Division Matchup` | FBS_P4 vs FCS is the single highest-risk cell on the board |
| `Model SD` | Per-game implied SD, visible next to the mean |
| `H1/FG Ratio` | Printed per game so a degenerate ratio is visible without computing it |
| `Model MAE (rolling)` | Model's trailing error on that market family |
| `Book MAE (rolling)` | Same for the market — the comparison must be on the board, not in an audit |

**Board 4 — Master EV+:**

- Add `Model-vs-Book MAE ratio` per market family. Any family where model MAE > book MAE is capped at WATCH, no exceptions.
- Add `Edge vs Vig` — flag any row whose edge in probability points is smaller than the vig it pays. Five rows on this slate qualified.
- Collapse duplicate economic positions **before** ranking, not after. Eight rows collapsed to four positions on this slate.

**Board 5 — Distribution:** print `P10–P90 width` as an explicit column with a `WIDTH_IMPLAUSIBLE` flag above 45 points.

**New Board 10 — RANK INTEGRITY / CALIBRATION.** Every run, using the trailing settled sample:

```text
| Metric                                  | This run | Trailing | Threshold | Status |
| Brier: P_MC                             |          |          | < 0.2500  |        |
| Brier: P_CONSERVATIVE                   |          |          | < market  |        |
| Brier Skill Score vs market             |          |          | > 0       |        |
| Spearman(EV_CONS, outcome)              |          |          | > +0.10   |        |
| Spearman(confidence, outcome)           |          |          | > +0.10   |        |
| Beat-close rate, exact-line rows only   |          |          | > 52%     |        |
| Top-quintile ROI minus bottom-quintile  |          |          | > 0       |        |
| Positive-EV hit rate vs required        |          |          | >= req    |        |
```

This slate would have scored: 0.3056 FAIL · 0.2554 FAIL · −0.0358 FAIL · −0.294 FAIL · 0.000 FAIL · 46.4% FAIL · −94.0pp FAIL · 25.0% vs 51.5% FAIL. **Eight for eight.** A board like this makes the failure visible on the desk instead of requiring a postgame forensic pass.

## 8.5 Confidence score

The score is inert (ρ = 0.000 against both outcome and CLV) while being the primary ranking key of the V1.1 prompt. Two acceptable paths:

1. Feed it real inputs — `component_sample_size` cannot stay pinned at 0.00 — and re-validate discrimination before it ranks anything again; or
2. Stop publishing it as a ranking key and rank on a validated field.

Publishing an inert score as the primary sort order is worse than publishing no score, because it manufactures the appearance of a hierarchy.

## 8.6 CLV instrumentation

Ladder translation over a broken ladder produced soft CLV on 104 of 132 rows. Going forward:

- Capture **both sides at the entry line** at close, not merely both sides at the closing line. This makes exact-line CLV available on every row and removes the translation entirely.
- Emit `ladder_translation_used` as a boolean on every CLV row so soft measurements are never silently pooled with clean ones.
- Weight calibration promotion on exact-line CLV only.

---

# 9. CALIBRATION DECISION

```text
Model:                  ncaaf_mc_totals_v1.1.0
Run:                    NCAAF_2026_W01_d20e9fbf30
Calibration decision:   FAILED — DO NOT PROMOTE
Stake status:           DISABLED_UNTIL_CALIBRATED (unchanged)
Real-money:             NOT AUTHORIZED
Re-entry requirement:   M1-M4 implemented, 8.3 gates live, Board 10 green on a
                        held-out slate before any VALUE/ELITE grade is issued.
```

**A caution against the obvious wrong lesson.** The inverse correlation is real and significant on this slate, but fading this model is not a strategy. The inversion is a symptom of one structural defect — opponent-independent team scoring in a week loaded with FBS-vs-FCS mismatches — not a durable exploitable signal. Fix M1 and the inversion should disappear rather than flip to a positive edge. One 142-row slate with a structurally broken input tells you the model is broken; it does not tell you what the corrected model's edge would be, in either direction.

**On sample size.** n = 142 rows across 11 games with heavy same-game correlation is not 142 independent observations; effective n is closer to the game count. The findings that survive this caveat are the ones that do not depend on the betting outcomes at all: model team-total MAE of 18.83 against a book at 7.69, an H1/FG ratio SD of 0.0004 against a realized 0.1140, and a raw Brier of 0.3056 against a coin flip's 0.2500. Those are measurements of the model against reality, and they are conclusive on their own.

---

# 10. AUDIT TRAIL

```text
Handoff integrity:        18/18 files, 18/18 sha256 + byte counts verified
Frozen values modified:   0
Probabilities recomputed: 0
Fabricated values:        0
DATA GAP rows:            10 CLV rows (declared), kickoff timestamps (all files)
Close labels used:        CLOSE_PROXY_PUBLIC (75), UNVERIFIABLE (5), TRUE_CLOSE (0)
Boundary:                 Python prices; Trading Agent audits, ranks, risk-filters, records.
                          Preserved throughout. Calibration feedback belongs to future
                          Python versions and has not been retro-applied to this frozen run.
```

```text
Bottom line: the casino-quant score is 0/3 — high-ranked model edge did not beat the close
(46.4% on clean rows, p=0.851), did not price correctly (Brier 0.3056 raw versus 0.2500 for a
coin flip and a Brier Skill Score of -0.0358 against the market), and did not outperform
lower-ranked edge but significantly underperformed it (Spearman -0.294, p=0.0004), with the
28 positive-EV rows going 7-21 for -51.63% while the 114 rejected rows returned +5.87%; all
four desk-raised blocking flags were confirmed, real-money authorization was correctly
withheld, and ncaaf_mc_totals_v1.1.0 is graded FAILED — DO NOT PROMOTE pending opponent
adjustment, division-tier priors, independent halftime-state derivation, and latent-sigma
re-scaling.
```
