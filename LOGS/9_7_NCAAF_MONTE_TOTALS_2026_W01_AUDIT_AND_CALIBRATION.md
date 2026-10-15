# NCAAF MONTE CARLO TOTALS — FORMAL SLATE AUDIT & CALIBRATION REPORT
## Run `NCAAF_2026_W01_d1084683a0` · Slate 2026-09-07 · SMU Mustangs @ Florida State Seminoles

| Field | Value |
|---|---|
| Report type | Post-slate Audit + Calibration + Board/Pipeline Improvement Ticket Set |
| Report authority | External NCAAF Trading Agent (Command Center layer) |
| Model version audited | `ncaaf_mc_totals_v1.1.0` (frozen, unmodified) |
| Pipeline version | `1.1.0` · feature version `ncaaf_features_v1.1` |
| Prompt version | `NCAAF_MONTE_TOTALS_USER_INPUT_PROMPT_V1_1_CONFIDENCE_RANKED.md` |
| Simulation | 250,000 paths · seed `20260901` · converged (Δp 0.001654 vs tol 0.0075) |
| Slate scope | 1 modeled game · 5 distinct markets · 11 book×market pairs · 22 priced rows |
| Result source | seminoles.com opponent history · captured `2026-09-10T10:48:19Z` |
| Close source | Public archives (SportsbookReview, ats.io, BallKnowMe) · captured `2026-09-10T10:48:19Z` / `11:19:13Z` |
| Close label | `CLOSE_PROXY_PUBLIC` on 11/11 rows — **no `TRUE_CLOSE` claimed** |
| Real-money exposure | **NONE** — slate was `PAPER_ONLY / RISK_ROOM_REVIEW` throughout |
| Calibration status | `UNCALIBRATED` — **unchanged by this report** |
| Frozen record | **UNMODIFIED** — no probability, EV, fair total, correlation or distribution altered |

---

# PART I — EXECUTIVE VERDICT: THE CASINO-QUANT SCORE

## The question posed

> *Did high-ranked model edge consistently beat the close, price correctly, and outperform lower-ranked edge across the slate?*

## The answer

**NO on all three counts — and one of the three failures is structural, not statistical.**

| Test | Result | Verdict |
|---|---|---|
| **1. Did high-ranked edge beat the close?** | Spearman(confidence rank, no-vig CLV) = **−0.762** | **FAILED — inverted** |
| **2. Did the model price correctly?** | Brier: model 0.25932 vs close 0.25522 · LogLoss: model 0.71176 vs close 0.70359 | **FAILED — market marginally better** |
| **3. Did high-ranked edge outperform low-ranked edge?** | Top tier 0-5, mean CLV −0.16pp, 2/5 beat close · Bottom tier 1-2, mean CLV **+1.37pp**, **3/3** beat close | **FAILED — inverted** |

### The decisive caveat, stated before anything else

**Tests 1 and 3 rest on n = 8 rows drawn from a SINGLE GAME.** The frozen correlation matrix reports pairwise ρ up to **+0.774** between these positions. The effective independent sample size is approximately **one**, not eight. A Spearman of −0.762 on one correlated game is **not evidence that the ranking law is wrong**. It is one observation, and it is recorded as such.

**Test 2 is likewise n = 4 markets.** A Brier gap of 0.0041 is far inside noise.

### What is NOT inside noise

**Finding CAL-01 does not depend on sample size at all.** It is provable from the frozen handoff arithmetic alone, and it explains the −0.762 mechanically:

> **The confidence score — the V1.1 primary ranking variable — is, within this slate, an exact linear function of `component_model_market_agreement` and nothing else.**
>
> ```text
> confidence = 56.4499 + 10.0132 × component_model_market_agreement
> max absolute residual across all 22 rows = 0.0029  (pure display rounding)
> ```
>
> Eight of the nine confidence components are **constant across every row**. Only market agreement varies.
>
> **Consequence:** "high confidence" currently means "the model agrees with the price." Agreement with the price is the definition of **no edge**. The V1.1 ranking law therefore sorts the **lowest-edge rows to the top of every board, by construction.**

This is the single most important output of this audit. The −0.762 rank correlation is not a surprising empirical result — it is the arithmetically predicted consequence of ranking by a variable that is an inverse proxy for edge. **Any slate run under the current confidence formula will reproduce this inversion.**

## Slate scorecard

```text
Settlement:            SMU 27, Florida State 24 (halftime SMU 17-10), no OT
                       FG total 51 | H1 total 27 | FSU 24 | SMU 27
                       ALL FIVE MARKETS LANDED UNDER — zero pushes (all half-point lines)

Official card (Board 4, EV_CONSERVATIVE > 0):   0-2   -2.000u / 2.000u    ROI -100.00%
Confidence ladder (Board 9, best price/family): 1-4   -3.048u / 5.000u    ROI  -60.95%
All 22 priced rows (both sides):               11-11  -1.592u / 22.000u   ROI   -7.24%
  OVER sides:                                   0-11 -11.000u             ROI -100.00%
  UNDER sides:                                 11-0   +9.408u             ROI  +85.53%
Model lean accuracy:                            1 of 5 markets
Distribution accuracy:                          PASS — all 4 realized values in 42nd-50th percentile
CLV, measurable ladder picks:                   3 of 3 positive (+1.08, +0.55, +2.61 pp)
Close coverage:                                 11 of 11 entry pairs — complete
```

## The paradox that defines this slate

The model **beat the closing line on every measurable ladder pick and lost four of five bets.** Simultaneously, its Monte Carlo distribution placed all four realized values between the 42nd and 50th percentile — near-textbook distributional accuracy — while its *line leans* went 1-for-5.

These are not contradictory. They decompose cleanly:

- **The distribution engine is sound.** No tail event, no anomaly, median error ≤ 4 points on every series.
- **The edge-extraction layer is unproven and mis-ranked.** It converted a sound distribution into four wrong directional calls, and it ranked them in inverse order of their own quality.
- **The market made the same directional error.** On FG and H1 the closing market moved *toward* the model's side and both were wrong together. That is shared error, which is why positive CLV coexists with a losing card.

---

# PART II — GRADING & SETTLEMENT

## II.1 Settlement facts

```text
SMU Mustangs 27, Florida State Seminoles 24 — FINAL, no OT (ot_periods = 0, reg == final)
Halftime: SMU 17, Florida State 10
FG TOTAL = 51    H1 TOTAL = 27    FSU (home) = 24    SMU (away) = 27
```

| Market | Line | Actual | Margin | Settled | Model lean | Lean correct? |
|---|---:|---:|---:|---|---|---|
| FG total | 54.5 | 51 | −3.5 | UNDER | OVER | ✗ |
| FSU team total | 26.5 | 24 | −2.5 | UNDER | OVER | ✗ |
| SMU team total | 28.5 | 27 | −1.5 | UNDER | UNDER | **✓** |
| H1 total | 27.5 | 27 | −0.5 | UNDER | OVER | ✗ |
| H1 total (alt strike) | 32.5 | 27 | −5.5 | UNDER | OVER | ✗ |

All five settlement lines were half-points. **Zero pushes**, matching frozen `p_push = 0.0` on all 22 rows. Team totals graded on final scores; no OT adjustment required.

## II.2 Official card grade — Board 4

| Rank | Bet | Book | Price | EV_CONS at entry | Result | P/L |
|---:|---|---|---:|---:|---|---:|
| 1 | H1 OVER 32.5 (alt) | BetMGM | +200 | +26.21% | **LOSS** | −1.000u |
| 2 | H1 OVER 27.5 | DraftKings | +102 | +0.33% | **LOSS** | −1.000u |

```text
Record 0-2 | P/L -2.000u | ROI -100.00%
```

**Concentration risk materialized exactly as forecast.** Both official rows were H1 OVER on the same game at supplied ρ **+0.774**. The pre-game Board 7 exposure warning stated they were one economic position at two strikes. They failed together. This is a **single** losing position expressed twice, not two independent losses — and it is a live demonstration of why the duplicate-exposure rule exists.

## II.3 Confidence ladder grade — Board 9

| Rank | Conf | Pick | Price | Result | P/L | no-vig CLV |
|---:|---:|---|---:|---|---:|---:|
| 1 | 66.11 | FG OVER 54.5 (FanDuel) | −110 | LOSS | −1.000u | **+1.08pp** |
| 2 | 65.58 | FSU TT OVER 26.5 (FanDuel) | −115 | LOSS | −1.000u | GAP (line moved against) |
| 3 | 64.97 | SMU TT UNDER 28.5 (BetMGM) | −105 | **WIN** | **+0.952u** | **+0.55pp** |
| 4 | 64.69 | H1 OVER 27.5 (DraftKings) | +102 | LOSS | −1.000u | **+2.61pp** |
| 5 | 63.28 | H1 OVER 32.5 alt (BetMGM) | +200 | LOSS | −1.000u | GAP (strike withdrawn) |

```text
Record 1-4 | P/L -3.048u | ROI -60.95%
```

---

# PART III — THE CASINO-QUANT SCORE, IN FULL

## III.1 Methodology

Two CLV measures are computed. Both use the same book, side and line on entry and close.

```text
priceCLV  = implied(close price) − implied(entry price)          [both vigged, same book]
noVigCLV  = fair_close(side) − P_MARKET_FAIR_entry(side)         [both de-vigged, same book]
```

`P_MARKET_FAIR` is the frozen de-vigged entry probability from `02_MASTER_EV_BOARD.csv`. `fair_close` de-vigs the supplied two-sided closing price by proportional normalization. **Positive = the market moved toward our side = we beat the close.**

The test population is the **8 distinct book×market pairs where the model had a directional lean and a same-line close exists.** Rows where the line moved (3) or the strike was withdrawn (1) cannot yield a like-for-like CLV and are excluded from the correlation, then handled directionally.

## III.2 Test 1 — Did high-ranked edge beat the close?

| Conf rank | Confidence | Position | Book | Entry | Close | no-vig CLV | price CLV | Result |
|---:|---:|---|---|---:|---:|---:|---:|---|
| 1 | 66.11 | FG OVER 54.5 | DraftKings | −118 | −115 | **−0.65pp** | −0.64pp | LOSS |
| 2 | 66.09 | FG OVER 54.5 | BetMGM | −125 | −115 | **−0.61pp** | −2.07pp | LOSS |
| 3 | 65.58 | FSU TT OVER 26.5 | BetMGM | −118 | −112 | **−0.96pp** | −1.30pp | LOSS |
| 4 | 65.54 | FG OVER 54.5 | BetRivers | −113 | −114 | +0.32pp | +0.22pp | LOSS |
| 5 | 65.41 | FG OVER 54.5 | FanDuel | −110 | −115 | +1.08pp | +1.11pp | LOSS |
| 6 | 64.96 | H1 OVER 27.5 | FanDuel | −102 | −105 | +0.95pp | +0.72pp | LOSS |
| 7 | 64.69 | H1 OVER 27.5 | DraftKings | +102 | −110 | **+2.61pp** | **+2.88pp** | LOSS |
| 8 | 64.08 | SMU TT UNDER 28.5 | BetMGM | −105 | −108 | +0.55pp | +0.70pp | **WIN** |

```text
Spearman(confidence, noVigCLV) = -0.762
Spearman(confidence, priceCLV) = -0.762
Spearman(confidence, P/L)      = -0.577
```

**The three worst CLV rows are the three highest-confidence rows. The best CLV row is the second-lowest confidence. The only winner is the lowest confidence.** The relationship is monotonically inverted across the board.

## III.3 Test 3 — Tier comparison

| Tier | n | Mean no-vig CLV | Beat close | Record | P/L | ROI |
|---|---:|---:|---:|---|---:|---:|
| **TOP** (conf ≥ 65.41) | 5 | **−0.16pp** | **2 / 5** | 0-5 | −5.000u | −100.00% |
| **BOTTOM** (conf < 65.41) | 3 | **+1.37pp** | **3 / 3** | 1-2 | −1.048u | −34.93% |

The low-confidence tier beat the close **unanimously** and lost less. The high-confidence tier failed to beat the close on a majority of rows and lost everything.

## III.4 Test 2 — Did the model price correctly?

Scored against the de-vigged closing market on the four markets with same-line closes. Outcome `y = 0` (every OVER lost).

| Market | Model `P_MC` (OVER) | Close fair (OVER) | Model sq. error | Close sq. error | Model vs close |
|---|---:|---:|---:|---:|---:|
| FG 54.5 | 0.5262 | 0.5108 | 0.2769 | 0.2609 | +1.54pp |
| FSU TT 26.5 | 0.5394 | 0.5077 | 0.2909 | 0.2578 | +3.17pp |
| SMU TT 28.5 | 0.4482 | 0.5022 | **0.2009** | 0.2522 | **−5.40pp** |
| H1 27.5 | 0.5182 | 0.5000 | 0.2686 | 0.2500 | +1.82pp |

```text
Brier    model 0.25932  |  close 0.25522  ->  close better by 0.00410
LogLoss  model 0.71176  |  close 0.70359  ->  close better by 0.00817 nats
```

The market was marginally better on both proper scoring rules. **The gap is trivially small and n = 4 — this is a tie, not a defeat.** The model beat the close on exactly one market: SMU team total — which is also the only lean it won.

## III.5 Fair-value accuracy vs the book

| Market | Model fair | Book line | Actual | Model error | Book error | Closer |
|---|---:|---:|---:|---:|---:|---|
| FG total | 55.5 | 54.5 | 51 | 4.5 | 3.5 | Book |
| FSU TT | 27.5 | 26.5 | 24 | 3.5 | 2.5 | Book |
| SMU TT | 27.5 | 28.5 | 27 | **0.5** | 1.5 | **Model** |
| H1 total | 27.5 | 27.5 | 27 | 0.5 | 0.5 | Tie |
| **Mean abs error** | | | | **2.25** | **2.00** | Book by 0.25 |

**The most informative line in this report:** the only market where the model's fair number beat the book's is the only market where its lean won. Directional accuracy tracked numerical accuracy perfectly. At n = 5 this is anecdote — but it is a *coherent* anecdote, and it is the pattern to test forward.

## III.6 Model and market were wrong together

| Market | Market movement, entry → close | Model side | Both wrong? |
|---|---|---|---|
| FG 54.5 | fair OVER 0.5000 → 0.5108 at FanDuel (**+1.08pp toward OVER**) | OVER | **Yes** |
| H1 27.5 | fair OVER 0.4739 → 0.5000 at DraftKings (**+2.61pp toward OVER**) | OVER | **Yes** |
| FSU TT 26.5 | FanDuel line 26.5 → 25.5 (**1 pt against OVER**) | OVER | Model wrong, market right |
| SMU TT 28.5 | FanDuel line 28.5 → 27.5 (**1 pt toward UNDER**) | UNDER | **Both right** |

Externally sourced line history corroborates this (see Part VI): the full-game total drifted upward through the week from roughly 52.5 to 54.5. **The market was buying OVER into kickoff and the game landed 51.** The model was on the same side of that error.

**Interpretive discipline:** positive CLV that arises from moving *with* a market that is itself wrong is **not evidence of edge**. It is evidence of correlation with the market. Distinguishing "beat the close because we were sharp" from "beat the close because we drifted with a wrong market" requires many slates. This slate cannot distinguish them, and no claim is made either way.

---

# PART IV — CALIBRATION FINDINGS

Severity key: **P0** = blocks trust in board ranking · **P1** = materially degrades model quality · **P2** = hygiene/traceability · **P3** = documentation.

## CAL-01 (P0) — Confidence is an inverse proxy for edge

**Evidence.** All 22 rows of `09_MODEL_CONFIDENCE.csv`:

| Component | Value across all 22 rows |
|---|---|
| `component_data_quality` | CONSTANT 0.67 |
| `component_roster_qb_certainty` | CONSTANT 0.25 |
| `component_sample_size` | CONSTANT 0.00 |
| `component_simulation_convergence` | CONSTANT 1.00 |
| `component_market_pair` | CONSTANT 1.00 |
| `component_historical_calibration` | CONSTANT 0.50 |
| `component_weather_certainty` | CONSTANT 0.72 |
| `component_entity_resolution` | CONSTANT 1.00 |
| `component_model_market_agreement` | **VARIES — 22 distinct values, 0.682192 → 0.964529** |

```text
confidence = 56.4499 + 10.0132 × component_model_market_agreement
max abs residual across 22 rows = 0.0029
```

**Diagnosis.** Market agreement contributes ~10 points of a 100-point scale and is the *only* live term on a single-game slate. Because agreement rises as the model converges on the price, confidence rises as edge falls. Ranking Confidence DESC therefore ranks **anti-edge first**.

**This is a category error in the score's construction.** Confidence should measure the *epistemic reliability of the model's own estimate* — data quality, sample, convergence, roster certainty, weather certainty, entity resolution. Whether that estimate happens to agree with a sportsbook is a **separate, orthogonal quantity**. Blending the two produces a score that cannot serve as a ranking variable for edge.

**Corollary.** On a correctly-specified confidence score, this one-game slate should produce a **near-perfect tie** across all 22 rows — because all eight reliability components *are* identical. The observed 2.83-point spread is entirely spurious. The V1.1 ranking law was, on this slate, ranking noise.

## CAL-02 (P0) — `CONSERVATIVE_SHRINK_ARTIFACT` confirmed

**Flagged pre-game; the result reinforces rather than refutes it.**

`P_CONSERVATIVE` is produced by shrinking `P_BLEND` toward **0.50**, with shrink weight scaling inversely with confidence. On near-coin-flip lines this is genuinely conservative. On a strike materially away from a coin flip it is **anti-conservative**:

```text
H1 OVER 32.5 @ +200 (break-even 0.3333)
  P_MC           0.3920  ->  EV_RAW          +17.59%
  P_BLEND        0.3483  ->  EV_BLEND         +4.48%
  P_CONSERVATIVE 0.4207  ->  EV_CONSERVATIVE +26.21%   <-- MOST GENEROUS, labelled "conservative"
```

This was the **only** positive-EV row where `P_CONSERVATIVE` exceeded `P_MC` (by +2.87pp), and consequently the only row where `EV_CONSERVATIVE > EV_RAW`. It ranked **first** on the official card.

**The loss is not the evidence.** One +200 loss is fully consistent with a genuine 39% shot. The finding stands on arithmetic. Two independent facts corroborate it:

1. Actual H1 was 27 — the strike missed by 5.5 points.
2. **BetMGM withdrew the 32.5 strike entirely by close**, consistent with a thin alt rather than a sharp two-sided market.

**Impact.** Under any EV-proportional staking rule, ranking this row on +26.21% instead of its own `EV_BLEND` of +4.48% would have **oversized it by ~6×**.

## CAL-03 (P1) — Available current-season data was not ingested

Both team states are `PRIOR_SEASON_CFBD_CORE_SP_ELO` with `component_sample_size = 0.00` and `roster continuity 0.000`.

**Florida State had already played a full game.** Public reporting confirms an FSU Week 0 result against New Mexico State on 2026-08-29, with box-score detail (points, total yards, third-down rate, rushing yards) publicly available. The pipeline priced FSU off prior-season SP+/Elo while a current-season game existed in the record.

FSU was also the model's **largest single miss**: projected mean 29.46, actual 24 (−5.46). SMU, which genuinely had no 2026 tape, missed by only 1.93.

**This is not hindsight.** The Week 0 game predated the run by nine days.

## CAL-04 (P1) — `WEATHER_UNAVAILABLE` was avoidable and directionally relevant

The handoff carries `WEATHER_UNAVAILABLE:WARN` with `component_weather_certainty = 0.72`. Public game-day previews described warm, humid conditions in the low 80s with scattered showers and thunderstorms possible around kickoff and light wind.

Convective/humid conditions are a modest UNDER input. The model leaned OVER on 4 of 5 markets and every market landed UNDER. **No claim is made that weather caused the miss** — a 3.5-point FG miss is well inside normal variance. But the input existed, was retrievable, and was not used.

## CAL-05 (P1) — Alt strikes are not gated

`H1 32.5` entered the official card as **Rank 1** despite being an alt strike 5 points off the main line, quoted by a single book, at 6.67% vig, with no cross-book corroboration — and it was withdrawn by close. The pipeline treats it identically to a four-book main line.

## CAL-06 (P2) — Kickoff time absent from the handoff

No `commence_time` or kickoff field exists in any of the 18 files. Kickoff was publicly documented as 7:30 PM ET. Without it the agent cannot compute time-to-kick, assess price freshness against kickoff, or validate close-capture timing.

## CAL-07 (P2) — Slate coverage discrepancy unresolved

`slate_events = 1` while `08_MARKET_SNAPSHOT.csv` carries **81 distinct `odds_event_id` values / 508 price rows**. Because `commence_time` is absent, date-scoping of those 81 cannot be verified from frozen data. "100% model coverage" describes a one-game slate, not the NCAAF Week 1 board.

## CAL-08 (P2) — Odds ledger not attributable to run

`run_id` is **blank on all 30 rows** of `16_ODDS_API_USAGE_LEDGER.csv`. Attribution was performed by timestamp. This-run cost: 3 credits (0 + 1 + 2); ledger-wide 168 used / 332 remaining.

**Quota discipline itself: PASS.** V1 policy honoured exactly — `/events` discovery at zero cost, slate-wide `totals` at 1 credit, derivative `team_totals,totals_h1` on the shortlisted event only at 2 credits. No polling. No non-V1 markets. No calls initiated by the board run.

## CAL-09 (P2) — Edge drivers are game-level, not market-level

`edge_driver_2`, `edge_driver_3`, `risk_driver_1`, `risk_driver_2` are **identical strings across all 22 rows**. Only `edge_driver_1` (model-vs-market pp) is market-specific. Board 6 cannot differentiate why one market is preferred over another.

## CAL-10 (P2) — `freshness_status` column absent

`08_MARKET_SNAPSHOT.csv` has no `freshness_status` field. Status had to be inferred from `odds_stale` on the EV board plus computed capture lag (19–67s).

## CAL-11 (P3) — Close-capture taxonomy undefined and inconsistently applied

`capture_tier` T1/T2 appears in the closing file but is defined in no project protocol document. It is also applied inconsistently: H1 BetMGM and H1 DraftKings are **T1** while H1 FanDuel is **T2**, all three from the same SportsbookReview 1H matrix.

## CAL-12 (P3) — Team-total close sources are mixed

BetMGM team totals resolve via ats.io (no movement); FanDuel team totals via BallKnowMe (−1.0 pt on both teams). Books legitimately close at different numbers, so this is not necessarily a contradiction — but **the only two "line moved" team-total rows come from the single source that is not ats.io**. Move detection is source-dependent and should not be treated as confirmed market-wide movement.

## What the audit found working — do not regress these

| Area | Status |
|---|---|
| Distribution engine | **PASS** — all 4 realized values in the 42nd–50th percentile, no tail event, no `MODEL_DISTRIBUTION_ANOMALY` |
| H1 independence | **PASS** — genuine halftime simulation state; the prohibited `H1 = 0.5 × FG` shortcut is absent; H1 ladder shape differs materially from a halved FG ladder |
| Manifest integrity | **PASS** — 18/18 files, 18/18 sha256 + byte match |
| Push handling | **PASS** — `p_push = 0.0` correct on all half-point lines |
| Correlation matrix | **PASS** — internally consistent, ±1.0 complements, and its +0.774 warning **correctly predicted the official card's joint failure** |
| Odds API quota discipline | **PASS** — 3 credits, policy-compliant |
| Boundary preservation | **PASS** — `trading_agent_embedded=false`, `postgame_audit_embedded=false`, `close_capture_performed=false` |
| Close-label discipline | **PASS** — 11/11 `CLOSE_PROXY_PUBLIC`, no `TRUE_CLOSE` claimed, each justified |

---

# PART V — DISTRIBUTION ACCURACY

| Series | Actual | Model median | Model mean | Realized percentile |
|---|---:|---:|---:|---|
| FG total | 51 | 55.0 | 58.387 | **~42.9th** |
| H1 total | 27 | 28.0 | 29.505 | **~46.9th** |
| FSU points | 24 | 27.0 | 29.462 | **~42.5th** |
| SMU points | 27 | 27.0 | 28.925 | **~50.0th — exactly on median** |

Frozen ladders (unmodified):

```text
Total:  P05 23 | P10 28 | P25 41 | P50 55 | P75 74 | P90 92 | P95 103
H1:     P05  7 | P10 13 | P25 20 | P50 28 | P75 38 | P90 49 | P95  55
Home:   P05  7 | P10 10 | P25 17 | P50 27 | P75 40 | P90 52 | P95  60
Away:   P05  7 | P10 10 | P25 17 | P50 27 | P75 38 | P90 52 | P95  59
```

Every realized value landed in a narrow band between the 42nd and 50th percentile. **This is the strongest result in the entire audit.** A model going 1-for-5 on leans while placing all four realized values within 8 points of its own median does not have a broken distribution engine — it has a sound engine and an unproven, mis-ranked edge-extraction layer.

**Note the mean/median divergence.** FG mean 58.39 vs median 55.0 is a **+3.39 point right skew**. The model's own fair line (55.5) sits at the median, not the mean. Reading the 58.39 mean as the trade thesis misreads the board — the OVER lean was a 1-point line-value opinion, not a "58-point game" projection.

---

# PART VI — EXTERNAL SOURCING RECORD

Public sourcing was attempted for the one genuine CLV gap. Outcome and incidental findings recorded for traceability.

| Objective | Outcome |
|---|---|
| Recover BetMGM H1 **32.5 alt strike** closing price | **NOT RECOVERABLE.** Public archives carry full-game totals, spreads and moneylines; alt first-half strikes are not archived. `CLV_DATA_GAP` on Board 4 Rank 1 is **confirmed permanent** for this run. |
| Corroborate FG close 54.5 | **CORROBORATED.** Multiple independent outlets (FanDuel Research, CBS Sports) report the SMU–FSU total at 54.5 with −110/−110, consistent with the supplied close file and the frozen entry snapshot. |
| Recover pre-kick line history | **RECOVERED (incidental).** A game-day preview reports the total drifting upward from roughly 52.5 to 53.5 during the week; entry snapshot and close both show 54.5. The market was **moving OVER-ward into kickoff and the game landed 51.** |
| Kickoff time (CAL-06) | **RECOVERED (incidental).** 7:30 PM ET, Doak S. Campbell Stadium. |
| Weather (CAL-04) | **RECOVERED (incidental).** Warm and humid, low 80s, scattered showers/thunderstorms possible around kickoff, light wind. |
| FSU current-season data (CAL-03) | **CONFIRMED (incidental).** FSU played New Mexico State in Week 0 on 2026-08-29 with public box-score detail. |

**Sourcing discipline.** Nothing recovered here has been written back into the frozen handoff, used to alter any probability or EV, or used to construct a CLV figure. Incidental findings feed **forward-looking pipeline tickets only**. No `TRUE_CLOSE` label was upgraded. Tipster-site model predictions encountered during sourcing were disregarded as non-evidentiary.

---

# PART VII — PYTHON PIPELINE PATCH TICKETS

> **Governance.** Every ticket below is forward-looking. `ncaaf_mc_totals_v1.1.0` output for run `NCAAF_2026_W01_d1084683a0` is **immutable and unmodified**. No calibration is promoted. Nothing here is retro-fitted to this slate.

## PATCH-01 (P0) — Decompose confidence; strip market agreement out of it

**Addresses CAL-01.** The highest-priority change in this document.

```text
CURRENT:  confidence = f(data_quality, roster_qb, sample, convergence,
                         market_pair, historical_calibration, weather,
                         entity_resolution, MODEL_MARKET_AGREEMENT)

REQUIRED: model_reliability = f(data_quality, roster_qb, sample, convergence,
                                market_pair, historical_calibration, weather,
                                entity_resolution)          # NO agreement term

          market_concordance = component_model_market_agreement   # reported, NEVER ranked on

          edge_magnitude     = |P_CONSERVATIVE − P_BREAK_EVEN|    # the actual edge axis
```

Emit all three as separate columns in `09_MODEL_CONFIDENCE.csv` and every board file. **`model_reliability` replaces `confidence` as the V1.1 primary ranking variable.**

**Acceptance test:** on a single-game slate where all eight reliability components are constant, `model_reliability` must be **identical across all rows** (spread < 0.01). Under the current formula this slate produced a spurious 2.83-point spread. Add a regression test asserting this.

**Second acceptance test:** assert `corr(model_reliability, edge_magnitude)` is not structurally negative. Log the correlation each run; alert if it falls below −0.3.

## PATCH-02 (P0) — Fix the conservative shrink target

**Addresses CAL-02.**

```text
CURRENT:  P_CONSERVATIVE = shrink(P_BLEND -> 0.50, weight = g(confidence))
REQUIRED: P_CONSERVATIVE = shrink(P_BLEND -> P_MARKET_FAIR, weight = g(model_reliability))
```

Shrinking toward the de-vigged market anchor is conservative at every strike. Shrinking toward 0.50 is conservative only near coin flips and **actively inflates longshots**.

**Hard assertion, fail the run on violation:**

```python
assert EV_CONSERVATIVE <= EV_RAW + 1e-9, (
    f"CONSERVATIVE_SHRINK_ARTIFACT: {canonical_market_id} "
    f"EV_CONSERVATIVE={EV_CONSERVATIVE:.4f} > EV_RAW={EV_RAW:.4f}"
)
assert abs(P_CONSERVATIVE - 0.5) <= abs(P_BLEND - 0.5) or \
       abs(P_CONSERVATIVE - P_MARKET_FAIR) <= abs(P_BLEND - P_MARKET_FAIR)
```

**Also emit** `EV_FLOOR = min(EV_RAW, EV_BLEND, EV_CONSERVATIVE)` and make **`EV_FLOOR`, not `EV_CONSERVATIVE`**, the Board 4 inclusion gate. On this slate that gate would have reduced the official card from 2 rows to **1** (H1 OVER 32.5 `EV_FLOOR` = +4.48%; H1 OVER 27.5 `EV_FLOOR` = −0.24%, correctly excluded).

## PATCH-03 (P0) — Alt-line gating

**Addresses CAL-05.** Add to every board row:

```text
line_type            : MAIN | ALT
main_line_distance   : |alt_point − main_point|
book_count_at_line   : integer
cross_book_corroborated : bool   (>= 2 books quoting the same strike)
```

Rules: exclude `ALT` from the official card **by default**; require `--allow-alt` to include. Any `ALT` row must be flagged `ALT_LINE_SINGLE_BOOK` when `book_count_at_line == 1`. Cap `main_line_distance` at 2.0 points for eligibility.

On this slate PATCH-03 alone removes the Rank 1 official-card row.

## PATCH-04 (P1) — Ingest current-season games; kill stale-state defaults

**Addresses CAL-03.** Before falling back to `PRIOR_SEASON_CFBD_CORE_SP_ELO`, query for completed current-season games per team. Emit:

```text
state_source              : CURRENT_SEASON | BLENDED | PRIOR_SEASON_FALLBACK
current_season_games_used : integer
state_asymmetry_flag      : true when the two teams have different game counts
```

`state_asymmetry_flag` is important: FSU had one 2026 game and SMU had none. Asymmetric information quality between the two sides of a total is a real risk driver and is currently invisible.

## PATCH-05 (P1) — Weather ingestion with explicit failure taxonomy

**Addresses CAL-04.** Replace binary `WEATHER_UNAVAILABLE` with:

```text
WEATHER_RESOLVED | WEATHER_FORECAST_ONLY | WEATHER_PROVIDER_FAILED | WEATHER_VENUE_UNMAPPED
```

Distinguishing "provider failed" from "indoor venue" from "not attempted" is necessary before weather certainty can be a meaningful confidence component. Retry on provider failure before degrading the component.

## PATCH-06 (P1) — Kickoff time is mandatory

**Addresses CAL-06.** Add `commence_time` (UTC) and `kickoff_local` to `00_MANIFEST.json`, `06_GAME_PROJECTIONS.csv`, `08_MARKET_SNAPSHOT.csv` and all board files. **Fail the handoff closed if absent** — the agent cannot assess price freshness or close-capture timing without it.

## PATCH-07 (P1) — Slate coverage reconciliation

**Addresses CAL-07.** Emit into `13_DATA_QUALITY_REPORT.json`:

```text
odds_events_discovered      : 81
odds_events_in_slate_window : <computed from commence_time>
espn_events_discovered      : 1
modeled_events              : 1
unmodeled_in_window         : [event_id, ...]
coverage_pct_of_window      : float
```

Raise `SLATE_COVERAGE_MISMATCH` when `espn_events_discovered` differs materially from `odds_events_in_slate_window`. Report coverage against the **window**, not against the count the pipeline happened to discover.

## PATCH-08 (P2) — Market-granular edge drivers

**Addresses CAL-09.** `edge_driver_2/3` and `risk_driver_1/2` must vary by `canonical_market_id`. Add a uniqueness assertion:

```python
assert edge_drivers.groupby('canonical_market_id')[
    ['edge_driver_2','edge_driver_3']].nunique().min() > 0, "EDGE_DRIVER_GRANULARITY_FAIL"
```

Where a driver genuinely is game-level, emit it in a separate `game_level_context` block rather than duplicating it across market rows.

## PATCH-09 (P2) — Snapshot freshness and ledger traceability

**Addresses CAL-08, CAL-10.**

```text
08_MARKET_SNAPSHOT.csv  += freshness_status  (FRESH | AGING | STALE | CRITICAL_STALE)
                        += capture_lag_seconds
                        += seconds_to_kickoff
16_ODDS_API_USAGE_LEDGER.csv : populate run_id on every row (currently blank on 30/30)
```

## PATCH-10 (P3) — Formalize close-capture taxonomy

**Addresses CAL-11, CAL-12.** Add `NCAAF_MONTE_TOTALS_CLOSE_CAPTURE_TIERS.md` defining T1/T2/T3 by evidence strength, not by source convenience:

```text
T1  direct book capture with last-offered timestamp        -> TRUE_CLOSE eligible
T2  archived book-specific price, book+line+both sides id'd -> CLOSE_PROXY_PUBLIC
T3  consensus/aggregate archive, book not identified        -> CLOSE_PROXY_CONSENSUS
```

Add `close_source_class` and require **two independent sources** before `line_moved = TRUE` is asserted (directly addresses CAL-12, where only one of two archives showed team-total movement).

---

# PART VIII — BOARD IMPROVEMENTS

## BOARD-01 — Replace the single ranking axis with a two-axis quadrant

The V1.1 law — "Confidence DESC, no exceptions" — was designed to stop large-but-fragile edges topping the board. That intent is correct and should be preserved. But with CAL-01 unfixed it ranks anti-edge first, which is worse than the failure mode it was written to prevent.

**Every ranked board should carry both axes and a quadrant label:**

| | **High edge** | **Low edge** |
|---|---|---|
| **High reliability** | `PRIME` — the only VALUE/ELITE-eligible quadrant | `NO_EDGE` — model agrees with the price; do not trade |
| **Low reliability** | `SPECULATIVE` — large gap, weak model; WATCH only | `DEAD` — no edge, no trust; PASS |

On this slate, with agreement stripped from reliability, **all 22 rows collapse into a single quadrant** (identical reliability, small edges) — correctly signalling that this slate offered nothing worth ranking. That is the honest board.

## BOARD-02 — Dual ladder on Board 9

Print two ladders, never one:

```text
9A — RELIABILITY LADDER : rank by model_reliability DESC  (which opinion do we trust most)
9B — EDGE LADDER        : rank by edge_magnitude DESC     (where is the disagreement largest)
9C — QUADRANT MAP       : the 2x2 above, with each row placed
```

Rank 1 of 9A answers "what do we believe." Rank 1 of 9B answers "where might money be." **Only rows appearing high on both are tradeable.** On this slate 9A would be a flat tie and 9B would put H1 OVER 32.5 first — and the quadrant map would place it in `SPECULATIVE`, not on the official card. That is the correct pre-game read, reached without hindsight.

## BOARD-03 — Board 4 gate hardening

```text
Inclusion gate:  EV_FLOOR > 0            (was: EV_CONSERVATIVE > 0)
Exclusion:       line_type == ALT        unless --allow-alt
Exclusion:       book_count_at_line < 2  for any strike off the main line
De-duplication:  max ONE row per correlation cluster where |rho| > 0.70
```

The de-duplication rule alone would have cut this slate's official card from 2 correlated H1 OVER rows to 1 — the supplied ρ was +0.774, above threshold. Combined with the `EV_FLOOR` and `ALT` gates, the correct official card for W01 was **zero rows**.

## BOARD-04 — New Board 10: Market Movement & CLV Forecast

The audit's most useful signal was line movement, which no pre-game board displayed. Add:

| Market | Entry fair | Prior snapshot fair | Drift pp | Direction vs model | Book dispersion | Vig range | Movement read |
|---|---:|---:|---:|---|---:|---:|---|

Purpose: surface **before** the bet whether the market is moving toward or away from the model's side, and whether books disagree. Requires retaining prior snapshots rather than only the latest.

## BOARD-05 — Print the mean/median divergence explicitly

FG mean 58.39 vs median 55.0 (+3.39 skew) was the most misreadable number on the board. Add a `Skew (mean − median)` column to Boards 1, 3 and 5, and print the model's fair line adjacent to it so the distinction between "fair line" and "mean projection" is unmissable.

## BOARD-06 — Surface state asymmetry on Boards 1–3

Add `State Asymmetry` per game (see PATCH-04). A total where one side has current-season data and the other has none carries a risk the current boards cannot express.

---

# PART IX — FORWARD TEST PROTOCOL

## IX.1 Why this slate cannot promote calibration

```text
Games:                                     1
Distinct markets:                          5
Book x market pairs:                       11
Priced rows:                               22
Max supplied pairwise correlation:         +0.774
EFFECTIVE INDEPENDENT OBSERVATIONS:        ~1
```

Twenty-two rows on one game is one observation wearing twenty-two hats. `calibration_status` remains `UNCALIBRATED`.

## IX.2 Sample size required

Two-sided α = 0.05, power = 0.80. **Independent games, not rows.**

**CLV (the fast metric):**

| Assumed per-bet CLV σ | Edge to detect | Games required |
|---:|---:|---:|
| 2.0pp | +1.0pp | **32** |
| 2.0pp | +0.5pp | **126** |
| 3.0pp | +1.0pp | **71** |
| 3.0pp | +0.5pp | **283** |

**ROI / win rate at −110 (break-even 52.38%):**

| True win rate | Bets required |
|---:|---:|
| 55.0% | **~2,800** |
| 54.0% | **~7,400** |

**Operational conclusion: grade the desk on CLV, not ROI.** CLV converges roughly two orders of magnitude faster. A season of NCAAF cannot produce 2,800 independent totals bets; it can plausibly produce enough games to resolve CLV.

## IX.3 Promotion gate

Do **not** promote `calibration_status` past `UNCALIBRATED` until all of:

```text
[ ] >= 50 independent games graded
[ ] >= 100 same-line close-proxy CLV observations
[ ] mean no-vig CLV > 0 at p < 0.05
[ ] Spearman(model_reliability, CLV) > 0 and stable across >= 3 monthly blocks
[ ] Brier(model) < Brier(close) on out-of-sample markets
[ ] PATCH-01 and PATCH-02 shipped and regression-tested
[ ] >= 30% of close captures at T1 (true close), not archive proxy
```

The fifth condition is the real bar. **A model that cannot beat the closing line's Brier score has no demonstrated edge**, regardless of realized ROI.

## IX.4 Per-slate metrics to log from now on

```text
spearman_reliability_vs_clv
spearman_reliability_vs_pl
mean_novig_clv | median_novig_clv | pct_beat_close
brier_model | brier_close | brier_delta
logloss_model | logloss_close | logloss_delta
realized_percentile per series (distribution calibration)
mean_abs_error_model_fair vs mean_abs_error_book_line
count_alt_line_rows | count_single_book_rows
count_correlated_pairs_on_card (|rho| > 0.70)
ev_floor_vs_ev_conservative_divergence_count
```

Build the PIT (probability integral transform) histogram of `realized_percentile` across slates. If the distribution engine is well calibrated it will be uniform. **This slate contributed four values in the 42nd–50th percentile — a promising start toward the middle of that histogram, and the metric to watch.**

---

# PART X — DATASET B RECORD

```text
record_id                     : NCAAF_2026_W01_d1084683a0_AUDIT
record_type                   : POST_SLATE_AUDIT_AND_CALIBRATION
model_version                 : ncaaf_mc_totals_v1.1.0
frozen_handoff_modified       : NO
calibration_promoted          : NO
real_money_exposure           : NONE (PAPER_ONLY / RISK_ROOM_REVIEW)

settlement                    : SMU 27, FSU 24 | H1 SMU 17, FSU 10 | FG 51, H1 27
markets_settled               : 5 of 5 UNDER | 0 pushes
official_card                 : 0-2 | -2.000u | ROI -100.00%
confidence_ladder             : 1-4 | -3.048u | ROI  -60.95%
all_priced_rows               : 11-11 | -1.592u | ROI -7.24%
model_lean_accuracy           : 1 of 5

spearman_confidence_vs_clv    : -0.762   (n=8, one game, rho up to +0.774 -> effective n ~1)
spearman_confidence_vs_pl     : -0.577
top_tier_mean_clv             : -0.16pp | beat close 2/5 | 0-5
bottom_tier_mean_clv          : +1.37pp | beat close 3/3 | 1-2
brier_model / brier_close     : 0.25932 / 0.25522  (close better by 0.00410)
logloss_model / logloss_close : 0.71176 / 0.70359  (close better by 0.00817)
mae_model_fair / mae_book     : 2.25 / 2.00
distribution_percentiles      : FG 42.9 | H1 46.9 | FSU 42.5 | SMU 50.0  -> PASS

close_coverage                : 11 of 11 entry pairs
close_labels                  : CLOSE_PROXY_PUBLIC x11 | TRUE_CLOSE x0
unrecoverable_gaps            : BetMGM H1 32.5 alt strike close (confirmed via external sourcing)

findings_P0                   : CAL-01 (confidence = inverse edge proxy)
                                CAL-02 (conservative shrink artifact)
findings_P1                   : CAL-03 (current-season data unused)
                                CAL-04 (weather avoidable)
                                CAL-05 (alt strike ungated)
findings_P2                   : CAL-06, CAL-07, CAL-08, CAL-09, CAL-10
findings_P3                   : CAL-11, CAL-12
patches_raised                : PATCH-01..10
board_changes_raised          : BOARD-01..06

casino_quant_verdict          : FAILED all three tests; test 3 (ranking) is STRUCTURAL
                                and reproducible from frozen arithmetic; tests 1 and 2
                                are statistically inconclusive at n=1 game
```

---

# PART XI — BOTTOM LINE

The W01 card lost every graded official play, the model's line leans went 1-for-5, and high-ranked model edge did **not** beat the close, did **not** price better than the closing market, and did **not** outperform lower-ranked edge — the rank/CLV relationship was inverted at **Spearman −0.762**.

At n = 1 game with supplied correlations to +0.774, that inversion is **not** by itself evidence against the ranking law. But the reason for it is: the confidence score is an exact linear function of model-market agreement (`confidence = 56.45 + 10.01 × agreement`, residual < 0.003, eight of nine components constant), which makes the V1.1 primary ranking variable a **direct inverse proxy for edge**. That finding is provable from the frozen handoff alone, requires no sample size, and will reproduce on every future slate until **PATCH-01** ships.

Set against that, the Monte Carlo distribution engine performed well — every realized value fell between the 42nd and 50th percentile with no tail event — and the correlation matrix correctly predicted the official card's joint failure before it happened. **The distribution is sound; the ranking and edge-extraction layer is not yet fit for capital.**

`calibration_status` remains `UNCALIBRATED`. The frozen handoff is unmodified. No real-money exposure occurred, and none is authorized.

---

*Prepared by the external AITA NCAAF Monte Carlo Totals Trading Agent. Python prices; the Trading Agent audits, ranks, risk-filters and records. All calibration feedback in this report is directed at future Python versions and has not been applied retroactively to run `NCAAF_2026_W01_d1084683a0`.*
