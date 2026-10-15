# NCAAF Monte Carlo Totals — Formal Audit, Calibration Report, and Board Upgrade Specification

**Run ID:** `NCAAF_2026_W01_04874fa5c8`
**Model version:** `ncaaf_mc_totals_v1.1.0`
**Slate:** 2026-09-05 · Season 2026 · Week 1
**Handoff frozen:** 2026-09-05T15:54:04Z
**Results captured:** 2026-09-07T18:48:51Z
**Audit performed by:** External Trading Agent (Command Center layer)
**Document status:** PERMANENT AUDIT RECORD — Calibration Sample 001
**Money at risk:** NONE. All rows were `PAPER_ONLY / RISK_ROOM_REVIEW`. Real-money authorization was never granted.

---

## 0. Executive answer to the quant question

> *Did high-ranked model edge consistently beat the close, price correctly, and outperform lower-ranked edge across the slate?*

**No, on all three counts. But the three failures are different in kind, and the distinction matters for what gets fixed first.**

| # | Question | Verdict | Strongest evidence |
|---|---|---|---|
| 1 | Did high-ranked edge beat the close? | **NO — but the ranking is uninformative, not inverted** | On the like-for-like set (entry line = close line, n=52 markets), rank vs price CLV is ρ = **+0.059, p = 0.680**. No relationship in either direction. |
| 2 | Did it price correctly? | **NO — negative skill against a coin flip** | `P_MC` Brier **0.25206** vs constant-0.500 baseline **0.25000** and vs entry market price **0.24580**. The model's probabilities are worse than knowing nothing. |
| 3 | Did high-ranked edge outperform low-ranked edge? | **NO — the ordering inverted, and the inversion is localised** | Top EV tercile **39.3% hit / −19.65% ROI**; bottom tercile **60.7% hit / +17.43% ROI**. The entire inversion lives in the deep alt-line rows. |

**The one-sentence casino-quant score:** the model produced no measurable edge, its probability estimates score worse than a coin flip, its internal ranking carries no closing-line information, and the only systematic signal in the ranking is a *negative* one manufactured by an over-wide distribution pricing deep alternate lines.

### 0.1 Methodological correction issued in this audit

An earlier pass of this audit reported a strong negative rank correlation against CLV (ρ = −0.531, p < 0.001) on the event-clustered set. **That figure is withdrawn as a like-for-like CLV measurement.** It conflated two different things:

- genuine line movement between entry and close; and
- the *depth* of an alternate line below or above the main number, because the public close archive recovered only the main number for alt-line rows.

For a row entered at `H1 OVER 28.5` whose close was recovered at the main number `23.5`, the −5.0 "line CLV" is not a market move. It is the alt-line depth restated.

The corrected treatment splits the graded set into a **like-for-like CLV set** (entry line = close line; CLV is pure price movement) and an **alt-line depth set** (close available only at the main number; CLV not computable, depth analysed separately). Every CLV claim below is scoped to one or the other. The withdrawn figure does not change any of the six blocker verdicts, all of which rest on other evidence.

---

## 1. Evidence base and scope

### 1.1 Inputs

| File | Rows | Role |
|---|---:|---|
| `NCAAF_MONTE_TOTALS_2026_W01_TRADING_AGENT_HANDOFF_04874fa5c8.zip` | 18 files | Frozen pregame handoff, SHA-256 and byte-count verified |
| `03_RESULTS.csv` | 68 | Final scores, all games |
| `04_CLOSING_LINES.csv` | 327 | Recovered closes |
| `05_MARKET_SETTLEMENTS.csv` | 327 | Settlement outcomes per entry line |
| `06_GAP_REGISTER.csv` | 39 | Documented unverifiable closes |

**No web sourcing was required.** The supplied closing-line capture covered every row that could be verified; the 39 unverifiable rows are documented in the gap register with reasons, and were correctly left as `DATA GAP` rather than substituted across books.

### 1.2 Derived test sets

The 654 priced rows in `02_MASTER_EV_BOARD.csv` cannot be rank-tested directly. They arrive as two-sided OVER/UNDER pairs at identical line, book and confidence. Within a pair one side always wins and one always loses, and line CLV is exactly symmetric. Any bucket built on the full 654 therefore returns **50.0% hit rate and 0.000 line CLV by construction**, regardless of model quality. This was verified empirically before proceeding.

| Test set | n | Construction | Used for |
|---|---:|---|---|
| **Full priced set** | 654 | All rows as issued | Gate selectivity, probability scoring |
| **Directional set** | 287 | Model-preferred side per market × book | Rank tests with book redundancy retained |
| **Event-clustered set** | 84 | One row per event × family × team, best EV | Primary rank test — removes book duplication |
| **Like-for-like CLV set** | 52 | Event-clustered, entry line = close line | **The only valid CLV test** |
| **Alt-line depth set** | 32 | Event-clustered, entry line ≠ close line | Depth analysis, not CLV |
| **Two-sided scored set** | 574 | Rows with a two-sided close and a settled outcome | Brier / log-loss / reliability |

Coverage: 61 of 68 events reach the scored set. 84 distinct economic markets. Every statistic below names its test set.

---

## 2. Question 1 — Did high-ranked edge beat the close?

### 2.1 The valid test: like-for-like CLV set (n = 52)

Entry line equals close line, so CLV is pure price movement in implied-probability points.

| Metric | Value |
|---|---|
| Mean price CLV | **+0.209 pp implied** |
| Beat / worse / unchanged | 14 / 7 / **31** |
| Beat rate | 26.9% (31 unchanged counted as not-beat) |
| Hit rate | 50.0% |
| ROI, flat 1u | −3.31% |

**Rank correlations against price CLV:**

| Ranking variable | ρ vs price CLV | p | ρ vs beat | p | ρ vs P/L | p |
|---|---:|---:|---:|---:|---:|---:|
| `EV_CONSERVATIVE` | +0.059 | 0.680 | +0.144 | 0.307 | −0.057 | 0.687 |
| `edge_pp` | +0.064 | 0.653 | +0.147 | 0.297 | −0.063 | 0.658 |
| `confidence` | −0.070 | 0.622 | −0.074 | 0.604 | −0.186 | 0.186 |

**Terciles, like-for-like set:**

| EV tercile | n | Hit | ROI | Price CLV pp | Beat rate |
|---|---:|---:|---:|---:|---:|
| Bottom | 18 | 55.6% | +7.21% | +0.232 | 22.2% |
| Middle | 17 | 47.1% | −9.00% | −0.071 | 17.6% |
| Top | 17 | 47.1% | −8.75% | +0.464 | 41.2% |

**Reading.** Nothing here is significant in either direction. Every p-value exceeds 0.29. The honest verdict is that **the model's ranking carries no closing-line information** — it is noise with respect to the close, not a reverse indicator.

Two structural caveats limit what this test can resolve at all:

1. **31 of 52 markets did not move.** The recovered closes are `CLOSE_PROXY_PUBLIC` archive snapshots, and on a Week 1 college slate most numbers sat still between the 15:52Z entry snapshot and the archived close. With 60% of the sample flat, CLV resolution on this slate is genuinely weak.
2. **n = 52 markets across 61 events in one week.** Even a real edge of 1–2% would not be detectable here.

The correct statement is therefore: *this slate cannot demonstrate closing-line edge, and it did not find any.* It is not evidence that the model reliably loses to the close — it is evidence that no edge was found where one would have to be.

### 2.2 The wider directional set (n = 195 same-line rows)

Retaining book redundancy for a larger sample:

| Metric | Value |
|---|---|
| Hit rate | 50.8% |
| ROI | −2.88% |
| Mean price CLV | +0.055 pp |
| `EV_CONSERVATIVE` vs price CLV | ρ = +0.118, p = 0.099 |
| `confidence` vs price CLV | ρ = +0.027, p = 0.704 |
| `confidence` vs P/L | ρ = −0.123, p = 0.086 |

Same conclusion, with the mild negative confidence-to-P/L drift approaching but not reaching significance. These rows are not independent — four books per market — so the effective n is closer to the 52 above.

### 2.3 Line-movement direction, full-game totals

| Direction | Count |
|---|---:|
| Line moved toward the model's side | 9 |
| Line moved away from the model's side | 10 |
| Line unchanged | 42 |

Nine versus ten. There is no anticipation of market movement in the model's leans.

---

## 3. Question 2 — Did the model price correctly?

### 3.1 Probabilistic scoring (two-sided scored set, n = 574)

| Estimator | Brier ↓ | Log-loss ↓ | Skill vs close |
|---|---:|---:|---:|
| `P_MC` (raw model) | **0.25206** | 0.69661 | **−0.0069** |
| `P_BLEND` | 0.24678 | 0.68630 | +0.0141 |
| `P_CONSERVATIVE` | 0.24800 | 0.68908 | +0.0093 |
| `P_MARKET_FAIR` (entry, devigged) | **0.24580** | **0.68425** | +0.0181 |
| `P_CLOSE_FAIR` (close, devigged) | 0.25033 | 0.69380 | — |
| Constant 0.500 baseline | 0.25000 | 0.69315 | −0.0013 |

**The raw model scores worse than a constant 0.500.** A forecaster who assigned 50% to every market on the slate would have beaten `P_MC` on both Brier and log-loss. The best estimator in the entire handoff is the one the model contributed nothing to: the devigged entry market price.

`P_BLEND` and `P_CONSERVATIVE` score better than `P_MC` only because they pull toward the market. The improvement measures how much market anchoring rescues the model, not how much the model adds.

Note the entry price outscoring the recovered close. On 574 correlated rows from a public archive this is not meaningful and should not be read as the entry snapshot being sharper than the close.

### 3.2 Reliability of `P_MC` (two-sided scored set)

| `P_MC` bin | n | Mean predicted | Realised | Gap |
|---|---:|---:|---:|---:|
| 0.00 – 0.35 | 20 | 29.3% | 45.0% | **+15.7pp** |
| 0.35 – 0.45 | 145 | 41.6% | 49.7% | +8.1pp |
| 0.45 – 0.50 | 122 | 47.6% | 43.4% | −4.2pp |
| 0.50 – 0.55 | 122 | 52.4% | 56.6% | +4.2pp |
| 0.55 – 0.65 | 145 | 58.4% | 50.3% | −8.1pp |
| 0.65 – 1.00 | 20 | 70.7% | 55.0% | **−15.7pp** |

Textbook over-confidence, symmetric and monotone. When the model says 70.7% it delivers 55.0%. When it says 29.3% it delivers 45.0%. Everything outside the middle needs to be pulled hard toward the market.

### 3.3 Reliability control — devigged closing price

| `P_CLOSE_FAIR` bin | n | Mean predicted | Realised | Gap |
|---|---:|---:|---:|---:|
| 0.45 – 0.50 | 351 | 49.5% | 51.6% | +2.1pp |
| 0.50 – 0.55 | 223 | 50.7% | 47.5% | −3.2pp |

The market is well calibrated inside 3 percentage points. The method used to score the model is sound — it validates on the control.

### 3.4 Reliability of `P_CONSERVATIVE` (directional set, n = 287)

| Bin | n | Predicted | Realised | Gap |
|---|---:|---:|---:|---:|
| ≤ 0.45 | 10 | 41.4% | 10.0% | **−31.4pp** |
| 0.48 – 0.50 | 32 | 49.4% | 46.9% | −2.5pp |
| 0.50 – 0.52 | 179 | 51.1% | 50.3% | −0.8pp |
| 0.52 – 0.55 | 63 | 52.7% | 52.4% | −0.3pp |
| > 0.55 | 3 | 56.3% | 100.0% | +43.7pp |

The 0.48–0.55 band, which holds 274 of 287 rows, is calibrated to within 2.5pp. This is the shrinkage working. The extremes are badly wrong but hold 13 rows total and should not be over-read.

---

## 4. Question 3 — Did high-ranked edge outperform low-ranked edge?

### 4.1 Event-clustered terciles (n = 84)

**By `EV_CONSERVATIVE`:**

| Tercile | n | Hit | ROI | Beat rate |
|---|---:|---:|---:|---:|
| Bottom | 28 | 60.7% | **+17.43%** | 66.7% |
| Middle | 28 | 42.9% | −17.33% | 47.4% |
| Top | 28 | 39.3% | **−19.65%** | 31.8% |

**By `confidence`:**

| Tercile | n | Hit | ROI | Beat rate |
|---|---:|---:|---:|---:|
| Bottom | 28 | 60.7% | **+17.27%** | 61.1% |
| Middle | 28 | 39.3% | −19.27% | 50.0% |
| Top | 28 | 42.9% | −17.55% | **23.5%** |

Both ladders run backwards, monotonically on hit rate for EV.

### 4.2 Where the inversion actually lives

Splitting the event-clustered set by whether the entry line was the main number:

| Segment | n | Hit | ROI | Mean claimed EV |
|---|---:|---:|---:|---:|
| **Same line as close (main number)** | 52 | 50.0% | −3.31% | +0.6% |
| **Alt line, 0.5–1.5 pts off** | 18 | 61.1% | +18.29% | +0.4% |
| **Alt line, 1.5–3 pts off** | 4 | 50.0% | −3.70% | −1.5% |
| **Alt line, 3+ pts off** | 10 | **10.0%** | **−69.00%** | **+33.0%** |

| Relationship | ρ | p |
|---|---:|---:|
| Alt-line depth vs claimed EV | **+0.654** | **0.0000** |
| Alt-line depth vs realised P/L | −0.332 | 0.0632 |

**This is the whole story in two rows.** The deeper the alternate line, the higher the EV the model claimed — ρ = +0.654 at p < 0.0001, an extremely tight mechanical relationship. And the deeper the line, the worse it performed. Ten markets sat more than 3 points off the main number carrying a mean claimed EV of **+33.0%**; they went **1 for 10** and returned **−69.00%**.

Every one of the top ten EV markets on the slate was an H1 alternate line 4–7 points off the main number:

| Matchup | Bet | Price | Claimed EV | Result |
|---|---|---:|---:|---|
| Central Michigan @ New Mexico | H1 OVER 28.5 | +240 | +46.48% | LOSS |
| Wyoming @ Colorado State | H1 OVER 28.5 | +240 | +45.58% | LOSS |
| Boston College @ Cincinnati | H1 OVER 31.5 | +250 | +44.42% | LOSS |
| Ohio @ Nebraska | H1 UNDER 19.5 | +275 | +34.90% | LOSS |
| Northern Illinois @ Iowa | H1 OVER 29.5 | +210 | +34.46% | WIN |
| Miami (OH) @ Pittsburgh | H1 UNDER 19.5 | +250 | +29.70% | LOSS |
| Oregon State @ Houston | H1 OVER 32.5 | +210 | +27.03% | LOSS |
| Tulane @ Duke | H1 OVER 30.5 | +180 | +24.40% | LOSS |
| Liberty @ James Madison | H1 OVER 30.5 | +180 | +22.56% | LOSS |
| Boise State @ Oregon | H1 UNDER 23.5 | +190 | +20.43% | LOSS |

**1 win, 9 losses.** Mean claimed EV +33.0%.

### 4.3 Family breakdown, event-clustered

| Family | n | Hit | ROI | Beat rate | Binomial p (hit) |
|---|---:|---:|---:|---:|---:|
| `FG_TOTAL` | 61 | 55.7% | +7.99% | 61.8% | 0.443 |
| `TEAM_TOTAL` | 11 | 36.4% | −30.41% | 37.5% | 0.549 |
| `H1_TOTAL` | 12 | **16.7%** | **−58.39%** | 0.0% | **0.0386** |

`H1_TOTAL` is the only family whose failure is individually significant. Full-game totals came out modestly positive but at p = 0.44 that is noise, and it should not be read as the FG board working — Section 6 shows the FG projection is negatively correlated with outcomes.

### 4.4 Was the gate itself selective? (full priced set, n = 654)

| EV family | Rows above 0 | ROI | Rows at or below 0 | ROI | Selective? |
|---|---:|---:|---:|---:|---|
| `EV_RAW` | 250 | −12.33% | 404 | −0.90% | No — inverted |
| `EV_BLEND` | 186 | −9.97% | 468 | −3.41% | No — inverted |
| `EV_CONSERVATIVE` | 79 | −10.21% | 575 | −4.59% | No — inverted |

All three gates selected worse rows than they rejected. The rows the pipeline promoted lost roughly twice as much as the rows it discarded.

---

## 5. Pregame blocker scorecard — prediction versus outcome

| # | Blocker | Predicted pregame | Observed postgame | Verdict |
|---|---|---|---|---|
| 1 | `MODEL_DISTRIBUTION_ANOMALY` | σ ≈ 25 vs realistic 13–15; tails far too fat | P10–P90 coverage **95.6%** vs 80%; P25–P75 **69.1%** vs 50%; **0 of 68** games above P90; realised RMSE **15.3** | **CONFIRMED** |
| 2 | `MODEL_DISCRIMINATION_COLLAPSE` | Flat projection, no matchup signal | corr(model, actual) **−0.132** vs book **+0.198**; MAE 13.06 vs 12.52; lean 31–30 | **CONFIRMED** |
| 3 | `CONSERVATIVE_EV_INVERSION` | Shrinkage to 0.500 inflates long-shot EV | Gate anti-predictive on all 654 rows; depth vs claimed EV ρ = **+0.654**, p < 0.0001 | **CONFIRMED** |
| 4 | `H1_FULL_GAME_INCONSISTENCY` | Ratio pinned to 0.5043–0.5063 cannot be real | Realised ratio **0.204–0.825**, σ 0.163; H1 family 2-for-12, p = 0.0386 | **CONFIRMED** |
| 5 | `CROSS_MARKET_CONFLICT` | Deep UNDER on events _006 and _012 is artifact | Both events: high-EV deep UNDER lost, low-EV main-number OVER won | **CONFIRMED** |
| 6 | `ALT_LINE_SHRINKAGE_ARTIFACT` | Plus-money alt-line EV manufactured | 3+ points off main: 1-for-10, −69.00% ROI on mean claimed EV +33.0% | **CONFIRMED** |

Six raised, six confirmed, none withdrawn. **The pregame decision to promote zero rows to VALUE or ELITE was correct.**

---

## 6. Calibration detail

### 6.1 Distribution calibration — full-game total (n = 68)

| Interval | Expected | Observed | Gap |
|---|---:|---:|---:|
| P05 – P95 | 90.0% | **98.5%** | +8.5pp |
| P10 – P90 | 80.0% | **95.6%** | +15.6pp |
| P25 – P75 | 50.0% | **69.1%** | +19.1pp |
| Below P10 | 10.0% | 4.4% | −5.6pp |
| **Above P90** | 10.0% | **0.0%** | −10.0pp |
| Below P05 | 5.0% | 1.5% | −3.5pp |
| **Above P95** | 5.0% | **0.0%** | −5.0pp |

```text
Model implied per-game sigma (from P10/P90)     ~25.2 points
Realised forecast RMSE, book number              15.32 points
Realised forecast RMSE, model fair total         15.84 points
Cross-game std deviation of actual totals        15.54 points

OVER-DISPERSION FACTOR                           ~1.63x
```

Not one game in 68 finished above the model's own 90th percentile. A calibrated distribution produces about seven. The upper tail the model was pricing does not exist in the sport — and that tail is precisely what generated the fake alt-line EV in Section 4.2.

First-half distribution, n = 14: P10–P90 coverage 85.7%, P25–P75 64.3%. Same direction, sample too small to weight.

### 6.2 Discrimination — model versus book (n = 62 priced games)

| Metric | Model fair total | Book total | Better |
|---|---:|---:|---|
| Mean absolute error | 13.06 | **12.52** | Book |
| Root mean squared error | 15.84 | **15.32** | Book |
| Correlation with actual | **−0.132** | **+0.198** | Book |
| Projection dispersion | σ 1.39 | σ 4.52 | Book |

**Model lean against the number (n = 61, pushes excluded):**

| Segment | n | Correct | Hit rate |
|---|---:|---:|---:|
| All leans | 61 | 31 | 50.8% |
| Lean OVER | 31 | 18 | 58.1% |
| Lean UNDER | 30 | 13 | 43.3% |
| Claimed edge 0–2 pts | 19 | 11 | 57.9% |
| **Claimed edge 2–5 pts** | 28 | 12 | **42.9%** |
| Claimed edge 5+ pts | 14 | 8 | 57.1% |

50.8% against a −110 break-even of 52.4%. The claimed edge size carries no positive information — the 2–5 point band, the meat of the distribution, hit below random.

### 6.3 First-half structure (n = 14 games with halftime data)

```text
                        minimum   maximum   spread   std dev
Model H1/FG ratio        0.5046    0.5059   0.0013     ~0.000
Realised H1/FG ratio     0.2041    0.8250   0.6209      0.163
```

Realised mean 0.4915. The model has the **centre** roughly right and **none of the variation**. It emits a constant where the sport produces a distribution 478× wider.

---

## 7. Statistical power — what this document does and does not establish

Read the two halves of this audit differently.

**Established, not sample-limited:**

- Distribution over-dispersion. n = 68 games, zero above P90, does not depend on prices or staking.
- Discrimination failure. n = 62, negative correlation with outcomes while the book is positive.
- H1 ratio degeneracy. A model spread of 0.0013 against a realised spread of 0.6209 is not a sample artifact at any n.
- The mechanical depth-to-EV relationship, ρ = +0.654 at p < 0.0001.
- `P_MC` scoring worse than a 0.500 constant on 574 rows.

**Directional only, requires 3–5 further slates:**

- The ROI figures. 84 correlated markets from one Week 1 slate.
- The tercile inversions. Suggestive, and consistent with the structural findings, but 28 markets per bucket.
- The confidence ladder inversion. Confidence this week was dominated by uniformly poor data-quality components — `MISSING_QB` and `WEATHER_UNAVAILABLE` on 68 of 68 games, `LOW_SAMPLE` on all — so it was measuring almost nothing.
- The FG family's +7.99% ROI. p = 0.44. Do not treat as the FG board working.

**Not established, explicitly:**

- That the model loses to the close. Section 2 found no relationship, not a negative one, and 60% of the sample did not move.
- That any repair will produce edge. These findings identify defects, not a path to profitability.

**Week 1 confound worth naming.** Every team state came from `PRIOR_SEASON_CFBD_CORE_SP_ELO`, 38 of 68 games used `DYNAMIC_SPARSE_PRIOR` on at least one side, and there was no weather, QB, or play-by-play data anywhere on the slate. A model with correct architecture would still perform poorly under those inputs. The defects in Sections 5 and 6 are architectural and would survive better data, but the magnitude of the failure is inflated by Week 1 conditions.

---

## 8. BOARD UPGRADE SPECIFICATION — Python pipeline

Everything below is for a future model version. **Nothing modifies the frozen W01 handoff, which stands exactly as issued.**

Ordered by expected impact per unit of engineering effort.

### 8.1 P0 — Halftime state must come from the sequential simulation

**Defect.** H1/FG mean ratio confined to a 0.0013 spread across 68 structurally different games, against a realised spread of 0.6209.

**Diagnostic to run first.** Instrument the drive loop and confirm whether the halftime snapshot is captured as game state at the end of the second quarter, or reconstructed from the full-game distribution afterwards. The ratio invariance is only explicable by the latter.

**Required changes.**

- Capture `h1_home_points_s` and `h1_away_points_s` inside the simulation loop at the halftime boundary, per path. Do not derive them.
- Emit `05_FIRST_HALF_TOTALS_BOARD.csv` from that per-path array only.
- Add the halftime state to `07_MONTE_CARLO_DISTRIBUTIONS.csv` as its own quantile set, computed independently rather than scaled.

**New assertion, fails the handoff:**

```text
ASSERT std(h1_mean_total / fg_mean_total across slate) > 0.02
  ELSE raise H1_RATIO_DEGENERATE -> BLOCK handoff
```

**New board column:** `h1_ratio_model`, `h1_ratio_slate_std` on `05_FIRST_HALF_TOTALS_BOARD.csv`, so the ratio is visible on the board rather than reconstructable only by audit.

**Interim safeguard until repaired.** Suppress `H1_TOTAL` from `02_MASTER_EV_BOARD.csv` entirely. This family went 2-for-12 and produced nine of the ten worst markets on the slate.

### 8.2 P0 — Reduce latent sigma from ~25 toward ~15

**Defect.** P10–P90 coverage 95.6% against 80% nominal. Zero of 68 games above P90.

**Required changes.**

- Recalibrate the drive-level and scoring-event variance terms until slate-level realised coverage sits inside nominal ± 6pp on the trailing sample.
- The handoff's own risk drivers already disclose the input: `mean latent sigma 0.280 / roster continuity 0.000` on 394 rows. Start there.

**New assertion, runs after every slate settles, fails the *next* handoff:**

```text
ASSERT 0.72 <= trailing_P10_P90_coverage <= 0.88
  ELSE raise DISTRIBUTION_MISCALIBRATED -> BLOCK handoff
ASSERT 0.02 <= trailing_above_P90_rate <= 0.18
  ELSE raise UPPER_TAIL_DEAD -> BLOCK handoff
```

This week's 95.6% and 0.0% would both have been caught before the ZIP was emitted, at essentially zero compute cost.

**New handoff file:** `19_CALIBRATION_LEDGER.csv` — one row per settled slate carrying coverage at each nominal quantile, realised RMSE, implied σ, and the assertion pass/fail. This is the file that makes calibration status a measured quantity rather than a declared one.

### 8.3 P0 — Change the conservative shrinkage target from 0.500 to market-fair

**Defect.** `P_CONSERVATIVE` shrinks toward 0.500. On a +240 price where break-even is 0.294, pulling probability up toward 0.500 is maximally aggressive. `EV_CONSERVATIVE` exceeded `EV_BLEND` on 327 of 654 rows.

**Required change.**

```text
CURRENT:  P_CONSERVATIVE = P_MC + k * (0.500 - P_MC)
REQUIRED: P_CONSERVATIVE = P_MC + k * (P_MARKET_FAIR - P_MC),  k in [0.5, 0.8] until calibrated
```

**New assertion, per row, fails the handoff:**

```text
ASSERT EV_RAW >= EV_BLEND >= EV_CONSERVATIVE  (within 1e-9)
  ELSE raise CONSERVATIVE_EV_INVERSION -> BLOCK handoff
```

Currently fails on **356 of 654 rows**. This single assertion would have blocked the W01 handoff before it reached the desk.

**Supporting evidence for the shrinkage magnitude.** The `P_MC` reliability table in Section 3.2 shows symmetric over-confidence of ±15.7pp at the extremes. `P_MARKET_FAIR` scored the best Brier of any estimator at 0.24580. Anchor hard to the market until the model earns otherwise.

### 8.4 P0 — Alternate-line governor

**Defect.** Alt-line depth predicts claimed EV at ρ = +0.654 (p < 0.0001) and predicts realised P/L at ρ = −0.332. Markets more than 3 points off the main number went 1-for-10 for −69.00% ROI on a mean claimed EV of +33.0%.

**Required changes.**

- Add `main_line` and `alt_line_depth = abs(point - main_line)` to `02_MASTER_EV_BOARD.csv` and to every family board. The desk currently has to reconstruct this by joining boards.
- Apply a depth penalty to EV before any board ranking, scaled to the calibration state of the tails.

```text
IF alt_line_depth > 1.5:
    quant_grade = ENTERTAINMENT              # cannot reach WATCH
IF alt_line_depth > 3.0:
    exclude from 02_MASTER_EV_BOARD entirely
    raise ALT_LINE_DEPTH_EXCLUDED on the row
```

This is a hard gate, not a haircut, and it stays until 8.2 demonstrates calibrated tails on the ledger.

**Rationale for hard exclusion.** Deep alt-line EV is not a small error, it is the model's largest claimed edge and its worst realised result simultaneously. Until tail calibration is proven, the correct EV for a deep alt line is "unknown," not "discounted."

### 8.5 P1 — Restore between-game discrimination

**Defect.** Model fair total dispersion σ 1.39 against market σ 4.52. Correlation with realised totals −0.132 while the book is +0.198. Model range 51.5–57.5 against a market pricing 44.5–66.5.

**Diagnostic to run first.** Confirm whether opponent adjustment is applied at all, or whether both teams are regressed to a shared league prior before entering the drive loop. The signature — too much variance *within* a game, too little *between* games — is what happens when team signal is absorbed into noise.

**New assertion:**

```text
ASSERT std(model_fair_total across slate) >= 0.55 * std(book_total across slate)
  ELSE raise MODEL_DISCRIMINATION_COLLAPSE -> BLOCK handoff
ASSERT corr(model_fair_total, book_total) >= 0.35
  ELSE raise MODEL_MARKET_DECORRELATED -> BLOCK handoff
```

W01 values: dispersion ratio 0.31, correlation −0.098. Both would have blocked.

**Note on the correlation gate.** A model that never disagrees with the market is worthless, so this floor is deliberately low. The point is that a total-projection model should recognise that Furman at Tennessee and Duquesne at Air Force are different games. Correlation of −0.098 means it does not.

### 8.6 P1 — Emit a market-blind and a market-aware board separately

**Defect.** `P_BLEND` and `P_CONSERVATIVE` both anchor to the market, and both outscore `P_MC`. That improvement measures market anchoring, not model skill — and the current board format makes it impossible to tell how much of any edge is the model's own contribution.

**Required change.** Add to `09_MODEL_CONFIDENCE.csv` or a new `20_MODEL_SKILL.csv`:

| Column | Meaning |
|---|---|
| `brier_mc_trailing` | Trailing Brier of `P_MC` against settled outcomes |
| `brier_market_trailing` | Trailing Brier of `P_MARKET_FAIR` |
| `brier_skill_vs_market` | `1 - brier_mc / brier_market` |
| `skill_status` | `NEGATIVE_SKILL` / `NO_SKILL` / `POSITIVE_SKILL` |

**New assertion:**

```text
IF brier_skill_vs_market < 0 over trailing >= 3 slates:
    stake_status = DISABLED_NEGATIVE_SKILL
```

W01 value: −0.0069 against the close, and worse than a 0.500 constant. The model currently has negative skill and the boards do not say so anywhere.

### 8.7 P2 — Confidence score must be tested, not asserted

**Defect.** The confidence ladder ran backwards this week — bottom tercile +17.27% ROI, top tercile −17.55% and a 23.5% CLV beat rate. The score is currently dominated by data-quality components that were uniformly poor.

**Required changes.**

- Decompose `confidence` into its components in the handoff and emit each separately: `component_data_quality`, `component_model_market_agreement`, `component_state_quality`, `component_convergence`, `component_roster_continuity`.
- Add trailing per-component rank correlation against realised CLV and P/L to `19_CALIBRATION_LEDGER.csv`.
- Do not use `confidence` as the primary board ranking key until at least one component demonstrates positive rank correlation over a 3-slate trailing window.

**Interim board law.** Rank on `EV_CONSERVATIVE` after the gates in 8.3 and 8.4, and display confidence as context rather than as the sort key. The V1.1 confidence-first ranking law has no empirical support yet in either direction.

### 8.8 P2 — Two-sided pair integrity in the EV board

**Defect.** The board issues both sides of every market as separate rows. Any bucket analysis on the full 654 returns exactly 50% hit rate and zero line CLV by construction, which silently defeats calibration work. This audit only avoided the trap by checking for it.

**Required changes.**

- Add `market_pair_id` (event × family × team × point × book) and `is_model_preferred_side` (boolean) to `02_MASTER_EV_BOARD.csv`.
- Add `economic_position_id` (event × family × team × side) so duplicate book rows collapse without the desk reconstructing the grouping.

Pregame the desk found 79 positive-EV rows collapsing to 49 distinct positions. That collapse should be a column, not an audit step.

### 8.9 P3 — Result and close capture contract

**Defect.** Only 14 of 68 games yielded halftime scores. The H1 structure test — the single most diagnostic finding in this audit — nearly did not run.

**Required changes.**

- If `H1_TOTAL` remains in the V1 market universe, halftime score capture becomes a required field in `03_RESULTS.csv`, not best-effort.
- Add `close_line_is_same_as_entry` (boolean) to `04_CLOSING_LINES.csv`. Without it, alt-line depth and genuine line movement are indistinguishable — the error this audit had to correct in Section 0.1.
- Add `close_price_only` (boolean) for rows where the number is unchanged and only the price moved, so like-for-like CLV can be filtered directly.

**Commendation on the existing capture.** Three corrupt archive cells were rejected rather than used: a FanDuel total of 71.5 at +340/−125 against a market near 58, a DraftKings total of 67.5 at +930/−3600 against a market near 44.5, and a DraftKings H1 cell of 30.5 at +222/−316 against consensus near 23.5. Cross-book substitution was refused where a required book had no two-sided pair. Using any of those would have manufactured enormous fake CLV. That discipline is why 39 rows are honestly unverifiable rather than quietly wrong, and it should be preserved verbatim in the capture spec.

### 8.10 P3 — Ledger housekeeping

- `16_ODDS_API_USAGE_LEDGER.csv` has `run_id` null on all 26 rows, breaching the required-field list in the Odds API credit protocol. The ledger cannot be attributed to its own run.
- `caesars` is requested in `regions_bookmakers` on all 26 calls and returns zero rows in `08_MARKET_SNAPSHOT.csv`, which holds only FanDuel (314), DraftKings (310), BetMGM (190) and BetRivers (180). Drop it or fix the mapping.

---

## 9. Promotion criteria — what must be true before any row can be staked

No row from this model reaches `VALUE` or `ELITE` until every line below reads PASS on the trailing ledger.

| # | Criterion | Threshold | W01 value | Status |
|---|---|---|---|---|
| 1 | P10–P90 coverage | 0.72 – 0.88 | 0.956 | **FAIL** |
| 2 | Above-P90 rate | 0.02 – 0.18 | 0.000 | **FAIL** |
| 3 | EV monotonicity `RAW ≥ BLEND ≥ CONS` | 100% of rows | 45.6% | **FAIL** |
| 4 | Model dispersion vs market | ≥ 0.55 ratio | 0.31 | **FAIL** |
| 5 | corr(model fair, book) | ≥ 0.35 | −0.098 | **FAIL** |
| 6 | H1/FG ratio slate std | ≥ 0.02 | ~0.000 | **FAIL** |
| 7 | Brier skill vs market, 3-slate trailing | > 0 | −0.0069 | **FAIL** |
| 8 | Confidence rank corr vs P/L, 3-slate trailing | > 0 | −0.183 | **FAIL** |
| 9 | Settled calibration slates | ≥ 4 | 1 | **FAIL** |

**9 of 9 failing. Calibration sample count: 1 of 4 minimum.**

---

## 10. Final ruling

```text
Frozen model status:         UNCHANGED — no retroactive modification of the W01 handoff
Calibration status:          UNCALIBRATED — this slate is sample 001, not a promotion
Real-money authorization:    NOT AUTHORIZED — unchanged
Desk blockers:               6 raised pregame, 6 confirmed postgame, 0 withdrawn
Pregame ruling:              promote nothing — UPHELD
Blocking assertions to add:  7 (sections 8.1 through 8.6)
New handoff files required:  19_CALIBRATION_LEDGER.csv, 20_MODEL_SKILL.csv
Markets suspended pending repair: H1_TOTAL (all), alt lines beyond 1.5 pts (all families)
```

**Casino-quant score for `ncaaf_mc_totals_v1.1.0` on slate 2026-09-05:**

> High-ranked model edge did not beat the close — the ranking carries no closing-line information (ρ = +0.059, p = 0.680 on the like-for-like set). The model did not price correctly — `P_MC` scores worse than a constant 0.500 and worse than the market it was trying to beat. High-ranked edge did not outperform low-ranked edge — the ordering inverted, with the top EV tercile at −19.65% against the bottom at +17.43%, and the entire inversion traceable to a mechanical +0.654 correlation between alternate-line depth and claimed EV. Four architectural defects are confirmed on evidence that does not depend on betting variance. The model is not yet a pricing engine; it is a candidate pricing engine with three blocking calibration failures and one degenerate market family.

---

*Grading performed by the external Trading Agent. Entry lines, prices, probabilities and distributions are frozen W01 handoff values, unmodified. Closing lines recovered from public archives and labelled `CLOSE_PROXY_PUBLIC`; no `TRUE_CLOSE` is claimed anywhere in this document. No future information has been backfilled into the pregame record. Calibration feedback belongs to a future Python version through the explicit promotion process in Section 9, never to this frozen output.*
