# NCAAF AITA MONTE CARLO TOTALS DESK V1
## Professional Data-Sourcing, Modeling, Odds-Management, and Trading-Agent Build Specification

**Season:** 2026 NCAAF  
**Primary objective:** Build a production-grade Python pipeline that prices college-football scoring distributions and searches for sustainable positive-EV opportunities in three primary market families:

1. **Full-Game Totals**
2. **Team Totals**
3. **First-Half Totals**

**Primary modeling engine:** Monte Carlo game simulation  
**Primary operating principle:** Price the football game first; compare to sportsbook prices second.  
**Downstream consumer:** AITA Trading Agent ZIP handoff  
**Baseline design source:** The prior NCAAF Monte Carlo Totals Trading Desk specification supplied by the user.

---

# 1. Executive decision: what data source should do what?

The correct architecture is **not** “use one API for everything.” It is a layered source hierarchy in which each provider performs the job it is best suited for.

## 1.1 Source hierarchy

| Source | Role | Priority | Cost sensitivity |
|---|---|---:|---:|
| **ESPN public/hidden JSON endpoints** | Schedule, event IDs, teams, rosters, athletes, box scores, results, play-by-play/game summaries, rankings, operational game identity | Primary | Very low / no paid quota, but unofficial |
| **CollegeFootballData (CFBD)** | Advanced football metrics, historical PBP, PPA/EPA-type fields, recruiting, ratings, opponent-adjusted data, historical validation | Quant enrichment / fallback | Free tier currently 1,000 calls/month |
| **The Odds API** | Current sportsbook prices for our targeted markets | Market-price source | **Scarce resource**: $0 Starter currently 500 credits/month |
| **Open-Meteo or equivalent weather feed** | Weather by stadium coordinates and kickoff time | Environmental source | Keyless/free for prototype/non-commercial use subject to provider terms |
| **Local AITA data warehouse** | Cached raw responses, normalized tables, engineered features, opening/entry/closing snapshots, audit trail | System of record | No external-call cost |

### Decision

**ESPN should be the primary operational source for team/player/game data, but it should not be the sole source of every advanced NCAAF metric.**

ESPN is well suited to:

- discovering the slate,
- resolving ESPN team and event IDs,
- obtaining rosters and player identities,
- retrieving game summaries and box-score statistics,
- obtaining play-by-play where available,
- resolving final scores and game status,
- maintaining a consistent event/player/team identity layer.

However, several features in the model specification—EPA/PPA, opponent-adjusted efficiency, recruiting strength, some advanced success/explosiveness measures, and historical college-football-specific analytics—are substantially easier and safer to obtain from CFBD or derive locally from play-by-play. Do **not** pretend ESPN has a documented, supported endpoint for every desired advanced metric.

The strongest architecture is therefore:

```text
ESPN = operational football truth / identity layer
CFBD = college-football analytics enrichment / historical quant layer
Open-Meteo = environment layer
The Odds API = scarce sportsbook price layer
AITA local warehouse = permanent system of record
```

---

# 2. Important ESPN implementation reality

ESPN's JSON endpoint ecosystem is widely used and follows similar patterns across football, basketball, baseball, hockey and other sports, but it is generally **undocumented/unofficial from a public developer-contract perspective**. The coding agent must therefore treat ESPN as a provider behind an adapter rather than embedding ESPN-specific JSON paths throughout the model.

## 2.1 Required architecture rule

Never write model code that directly assumes:

```text
response["foo"]["bar"][0]["baz"]
```

throughout the application.

Instead:

```text
ESPN raw JSON
    ↓
ESPN adapter/parser
    ↓
AITA normalized schema
    ↓
modeling code
```

If ESPN changes a response field, only the adapter should need repair.

## 2.2 ESPN endpoint families to test and support

The coding agent should validate these endpoints at build time rather than assuming every field is always populated.

### College-football scoreboard / slate discovery

```text
https://site.api.espn.com/apis/site/v2/sports/football/college-football/scoreboard
```

Useful filters commonly include date/week/season type.

Example pattern:

```text
.../scoreboard?dates=YYYYMMDD
```

or:

```text
.../scoreboard?week=WEEK&seasontype=2
```

Use this as the first source for:

- ESPN event ID
- home team
- away team
- kickoff
- venue if exposed
- status
- scores
- conference/team metadata

### Event summary

```text
https://site.api.espn.com/apis/site/v2/sports/football/college-football/summary?event={ESPN_EVENT_ID}
```

Use for:

- box score
- game leaders
- play-by-play where exposed
- drives where exposed
- scoring plays
- team statistics
- game state
- final score/status

### Team registry

```text
https://site.api.espn.com/apis/site/v2/sports/football/college-football/teams
```

and:

```text
.../teams/{TEAM_ID}
```

### Team roster

Test/support:

```text
.../teams/{TEAM_ID}/roster
```

Use for:

- ESPN athlete ID
- player name
- position
- class/year when present
- height/weight when present
- jersey
- active/current roster membership

### Team schedule

Test/support:

```text
.../teams/{TEAM_ID}/schedule
```

### Rankings

```text
.../rankings
```

Rankings are contextual information, not a direct model truth signal.

### Core API

ESPN also exposes core resource endpoints under patterns such as:

```text
https://sports.core.api.espn.com/v2/sports/football/leagues/college-football/...
```

These may provide athlete/team/event resources and references. The build should use them only after schema validation and should preserve raw responses.

## 2.3 ESPN across other sports

The important engineering lesson from ESPN's cross-sport endpoint families is that the **pattern is reusable**: scoreboard → event summary → team → roster/athlete → statistics. The same style of adapter design is useful in NFL, NBA/WNBA, MLB and other ESPN-covered sports.

Do not encode any claim of personal human “experience.” The implementation requirement is instead:

> Use the same proven endpoint-family pattern and defensive parsing approach commonly used for ESPN data across sports, while keeping the NCAAF adapter isolated and schema-tested.

---

# 3. Why CFBD should be part of V1

CFBD is a college-football-specific data source and materially reduces the amount of analytics infrastructure we must reinvent.

As of late August 2026, CFBD advertises a free API tier with **1,000 calls/month** and access to historical/core data, team and player statistics, recruiting data, betting lines, and advanced metrics. This is extremely useful for AITA because one well-filtered CFBD request can often replace dozens of fragile scrapes or custom calculations.

## 3.1 Use CFBD selectively—not as a high-frequency live poller

Recommended CFBD jobs:

- historical play-by-play
- PPA/EPA-related play fields where available
- success-rate inputs
- opponent-adjusted ratings
- SP+/SRS/Elo/FPI/CORE challenger ratings where available
- recruiting data
- historical team/player stats
- historical betting-line research
- validation of ESPN-derived features

## 3.2 Do not double-pay with calls

The system should cache all CFBD responses locally by:

```text
provider / endpoint / season / week / team / game_id / pulled_at
```

A historical response that cannot change should normally be pulled once and retained.

## 3.3 Historical PBP advantage

CFBD play records expose football-specific fields such as:

- game ID
- drive ID
- offense / defense
- quarter
- clock
- yard line / yards to goal
- down
- distance
- yards gained
- scoring flag
- play type
- play text
- PPA where available

This makes CFBD an excellent source for building and validating the possession/drive layer.

---

# 4. Data warehouse: the conductor of the concert

The external APIs are instruments. The **AITA local warehouse is the conductor**.

No production model should depend on repeatedly calling external services during simulation.

The correct flow is:

```text
EXTERNAL SOURCES
      ↓
RAW SNAPSHOT LAYER
      ↓
NORMALIZATION / ENTITY RESOLUTION
      ↓
FEATURE STORE
      ↓
MODEL INPUT SNAPSHOT
      ↓
MONTE CARLO
      ↓
MARKET PRICING
      ↓
EV / RISK
      ↓
TRADING AGENT ZIP
```

## 4.1 Raw layer

Persist every meaningful API payload exactly as received.

Suggested structure:

```text
data/
  raw/
    espn/
      scoreboard/
      teams/
      rosters/
      summaries/
    cfbd/
      games/
      plays/
      ratings/
      recruiting/
    odds_api/
      events/
      totals/
      event_markets/
    weather/
  normalized/
  features/
  snapshots/
  audits/
```

Every raw file needs metadata:

```text
provider
endpoint
request parameters
retrieved_at_utc
http_status
content_hash
schema_version
```

## 4.2 Never overwrite raw market data

Odds are time-series evidence.

Do not save:

```text
current_odds.json
```

and overwrite it every run.

Save timestamped snapshots:

```text
2026-09-05T14-00-00Z_odds.json
2026-09-05T16-30-00Z_odds.json
2026-09-05T17-45-00Z_odds.json
```

This is how the free plan can create our own historical line archive going forward.

---

# 5. Canonical entity registry

This is mandatory. Sports models fail when the same team has different names across providers.

Create canonical internal IDs:

```text
aita_team_id
aita_player_id
aita_event_id
```

Then maintain mappings:

| AITA field | ESPN | CFBD | Odds API |
|---|---|---|---|
| team ID | espn_team_id | cfbd_team_id/name | bookmaker participant name |
| player ID | espn_athlete_id | cfbd athlete ID when resolvable | not needed V1 |
| event ID | espn_event_id | cfbd_game_id | odds_event_id |

## 5.1 Matching hierarchy

Use deterministic matching in this order:

1. explicit saved provider ID mapping
2. exact normalized team name
3. aliases dictionary
4. home/away + date + kickoff tolerance
5. fuzzy match only as a flagged last resort

If an event cannot be confidently mapped, mark:

```text
ENTITY_RESOLUTION_FAILED
```

and **do not price it**.

---

# 6. Weekly data-ingestion concert

The pipeline should operate in phases so expensive data is only requested after inexpensive data has already narrowed the slate.

# Phase A — Slate discovery

### Source
ESPN scoreboard + Odds API `/events`.

### Cost
- ESPN: no Odds API credits.
- Odds API `/events`: currently does **not** count against Odds API usage quota.

### Output

```text
SLATE_EVENTS.csv
```

Fields:

```text
aita_event_id
espn_event_id
odds_event_id
home_team
away_team
kickoff_utc
kickoff_local
venue
conference_home
conference_away
neutral_site
fbs_fcs_flag
status
```

This becomes the authoritative slate manifest.

---

# Phase B — Team/roster refresh

### Source
ESPN teams/rosters.

### Frequency
- Full roster snapshot: once before first game of season.
- Weekly delta refresh: once weekly.
- Game-day refresh: only for teams on the slate if required.

### Store

```text
TEAM_MASTER
ROSTER_SNAPSHOT
PLAYER_MASTER
```

Do not re-download every team's entire roster on every model execution.

## 6.1 Roster continuity feature

Compare current roster with prior-season roster by athlete ID when possible.

Create:

```text
returning_player_pct
returning_qb_flag
returning_qb_production_share
returning_rb_production_share
returning_wr_production_share
returning_defensive_production_proxy
ol_continuity_proxy
roster_turnover_score
```

If ESPN does not expose a ready-made “returning production” statistic, derive continuity from athlete identity plus prior production.

---

# Phase C — Historical performance refresh

### Primary sources
- ESPN event summaries / box scores
- CFBD historical stats/PBP/advanced metrics

### Rule
Historical games already stored locally should not be re-fetched unless a parser/schema repair requires it.

### Build rolling windows

At minimum:

```text
last_3_games
last_5_games
season_to_date
previous_season
opponent_adjusted_current
```

Avoid a single “last game” feature dominating the model.

---

# 7. Mapping source data into the football layers

# 7.1 Layer: offensive scoring ability

## Raw inputs

From ESPN/CFBD:

- plays
- yards
- pass attempts/completions/yards/TD/INT
- rush attempts/yards/TD
- sacks
- third/fourth-down results
- red-zone attempts/scores where available
- turnovers
- scoring drives
- possessions/drives
- player production

## Derived features

```text
off_epa_per_play
off_success_rate
pass_epa_per_play
rush_epa_per_play
explosive_play_rate
yards_per_play
points_per_drive
scoring_opportunity_rate
points_per_scoring_opportunity
sack_rate_allowed
turnover_rate
red_zone_td_rate
```

Where ESPN lacks a directly supplied advanced metric, either:

1. calculate it locally from PBP under a versioned definition, or
2. obtain the metric from CFBD and label its source.

Never silently mix two definitions under the same column name.

Example:

```text
success_rate_source = "cfbd"
success_rate_definition_version = "cfbd_2026"
```

or:

```text
success_rate_source = "aita_derived"
success_rate_definition_version = "aita_sr_v1"
```

---

# 7.2 Layer: defensive scoring ability

Mirror offensive features from the defensive perspective:

```text
def_epa_allowed_per_play
def_success_rate_allowed
pass_epa_allowed
rush_epa_allowed
explosive_play_rate_allowed
points_per_drive_allowed
scoring_opportunity_rate_allowed
red_zone_td_rate_allowed
sack_rate_created
turnover_creation_rate
```

Do not use raw points allowed as the primary defensive measure; opponent quality and game state matter.

---

# 7.3 Layer: opponent adjustment

Every major team efficiency should have:

```text
raw_value
opponent_adjusted_value
sample_size
uncertainty
```

Possible sources:

- CFBD CORE/opponent-adjusted ratings
- internal iterative opponent adjustment
- Elo/SP+/FPI/SRS challenger ratings

AITA should not simply import a rating and call it truth. External ratings are **challengers/priors**.

---

# 7.4 Layer: QB/player impact

ESPN roster + athlete/game stats should build the player layer.

## QB priority fields

```text
starter_qb_id
qb_experience
qb_prior_attempts
qb_completion_pct
qb_yards_per_attempt
qb_td_rate
qb_int_rate
qb_sack_rate
qb_rush_share
qb_returning_flag
qb_transfer_or_new_team_flag_when_resolvable
qb_uncertainty
```

## Skill-player fields

```text
rb_carry_share
wr_target/reception_share_proxy
returning_receiving_yards_share
returning_rushing_yards_share
explosive_production_share
```

## V1 rule

Player data informs **team scoring strength**; V1 does not price player props.

---

# 7.5 Layer: preseason prior / Week 0 uncertainty

Use a weighted prior built from:

- previous-season opponent-adjusted offense/defense
- returning QB
- returning production proxies
- roster continuity
- recruiting/talent data from CFBD where available
- coaching/scheme continuity if a reliable source is implemented
- prior rating ensembles

Representation:

```text
team_offense_mean
team_offense_sigma
team_defense_mean
team_defense_sigma
special_teams_mean
special_teams_sigma
```

The key feature is **sigma**.

New QB + heavy roster turnover should not merely reduce the mean; it should widen uncertainty.

---

# 7.6 Layer: tempo and possessions

Derive from PBP/drives:

```text
plays_per_game
possessions_per_game
seconds_per_play_proxy
first_half_possessions
second_half_possessions
pass_rate
rush_rate
pace_when_leading
pace_when_trailing
pace_in_one_score_games
```

The possession engine should estimate a distribution:

```text
P(possessions = n)
```

not only a point estimate.

---

# 7.7 Layer: drive outcome probabilities

Historical drives should be normalized into:

```text
TD
FG
PUNT
TURNOVER
TURNOVER_ON_DOWNS
SAFETY
END_HALF
END_GAME
OTHER
```

Model conditional probabilities based on:

```text
offense strength
defense strength
starting field position
down/distance context aggregated at drive start
score differential
time remaining
home/away
```

The drive engine is what gives the Monte Carlo football-shaped scoring rather than Gaussian score noise.

---

# 7.8 Layer: explosiveness

Recommended versioned definitions:

```text
explosive_rush = rush >= threshold
explosive_pass = completed pass >= threshold
```

or use EPA/PPA-based explosiveness from CFBD when available.

Do not change thresholds midseason without versioning the model.

Store:

```text
explosive_rate_offense
explosive_rate_allowed
explosive_td_rate
```

---

# 7.9 Layer: turnovers

Separate stable skill from noisy result.

Build:

```text
interception_rate_thrown
fumble_rate
fumble_recovery_rate
turnover_created_rate
short_field_created_rate
non_offensive_td_rate
```

Shrink fumble recovery and extreme turnover margins strongly toward league average.

---

# 7.10 Layer: special teams

Use available box/PBP statistics for:

```text
fg_make_rate_by_distance_bucket
punt_net_yards
kick_return_efficiency
punt_return_efficiency
blocked_kick_rate
special_teams_td_tail
```

V1 can use modest weight with strong shrinkage.

---

# 7.11 Layer: game-state / blowout behavior

Derive team-specific tendencies if sample supports them; otherwise use pooled NCAA priors.

States:

```text
competitive
favorite_leading
underdog_trailing
blowout
end_half
```

Model changes to:

```text
pass_rate
tempo
drive aggressiveness
fourth_down_rate
starter_usage_proxy
points_per_drive
```

Large-spread college games require this layer. Do not use NFL-like assumptions.

---

# 7.12 Layer: weather

Weather must be resolved by:

```text
venue latitude/longitude
kickoff timestamp
forecast timestamp
```

Suggested variables:

```text
temperature_f
wind_speed_mph
wind_gust_mph
wind_direction
precip_probability
precip_amount
humidity
weather_code
```

**Wind should be modeled as a nonlinear interaction**, especially with passing volume and kicking distance. Never hardcode “rain = under.”

Cache stadium coordinates permanently.

---

# 8. The Monte Carlo orchestration

The Monte Carlo simulator is the centerpiece.

For every simulation `s`:

1. Draw uncertain team offensive/defensive latent strength.
2. Draw tempo/possession environment.
3. Apply matchup interactions.
4. Apply weather/environment.
5. Initialize possession, field position, clock, score and game state.
6. Simulate sequential drives.
7. Update game-state behavior after every scoring/clock change.
8. Store halftime score.
9. Continue through regulation.
10. Store final score and all market indicator variables.

Conceptually:

```text
FOR s in 1..N:
    draw latent team strengths
    draw tempo environment
    simulate drive sequence to halftime
    store H1 scores
    simulate second half with game-state transitions
    store final scores
    derive market outcomes
```

## 8.1 Simulation count

Support:

```text
100,000 minimum production mode
250,000 default final-board mode
500,000 optional verification mode
```

But convergence is the real requirement.

Create:

```text
MC_CONVERGENCE_REPORT.csv
```

Check key probabilities at increasing sample sizes.

If:

```text
abs(P_250k - P_500k) > tolerance
```

flag:

```text
SIMULATION_NOT_CONVERGED
```

---

# 9. Market outputs produced before calling the Odds API

This is a crucial cost-control rule.

The football model runs **before** expensive derivative-market calls.

For every game, Monte Carlo should generate a complete model-only record:

```text
mean_home_points
median_home_points
mean_away_points
median_away_points
mean_total
median_total
first_half_mean_total
first_half_median_total
score_percentiles
total_distribution
home_team_points_distribution
away_team_points_distribution
first_half_total_distribution
```

Then calculate probability curves across reasonable lines.

Example:

```text
P(total > 48.5)
P(total > 49.5)
...
P(total > 75.5)
```

and likewise for home/away team totals and 1H totals.

This means the model already knows which games are potentially interesting **before** asking The Odds API for scarce event-level derivative prices.

---

# 10. The Odds API: exact V1 market policy

## 10.1 Sport key

```text
americanfootball_ncaaf
```

## 10.2 V1 markets only

The pipeline is authorized to query these primary market keys:

```text
totals
team_totals
totals_h1
```

Optional later market:

```text
team_totals_h1
```

Do **not** query:

```text
h2h
spreads
player props
alternate markets
quarters
SGPs
```

unless a later model version explicitly enables them.

### Why

The mandate is to conserve usage credits and focus the market search on the three five-star market families.

---

# 11. Odds API credit economics

As of August 2026, The Odds API advertises a **$0 Starter plan with 500 credits/month**. The free plan includes current odds and all betting markets, but historical odds require a paid plan.

This has major architecture implications.

## 11.1 Free endpoints we should exploit

Current documentation states:

```text
GET /v4/sports
```

does not count against usage quota.

And:

```text
GET /v4/sports/{sport}/events
```

does not count against usage quota.

Use those for discovery.

## 11.2 Slate-wide featured total

The main odds endpoint can retrieve the full-game `totals` market for the slate.

Current quota formula:

```text
cost = number_of_markets × number_of_regions
```

Therefore:

```text
markets=totals
regions=us
```

normally costs only:

```text
1 credit
```

for the slate response.

That is extremely efficient.

## 11.3 Team totals and first-half totals

`team_totals` and `totals_h1` are additional markets and are queried **one event at a time** through the event-odds endpoint.

Current quota formula for current event odds:

```text
cost = unique markets returned × regions
```

Therefore an event request for:

```text
team_totals,totals_h1
```

with one region can cost up to:

```text
2 credits/event
```

This is why we must not call those markets for every NCAAF game blindly.

---

# 12. Two-stage Odds API scanner

This is the central quota-saving design.

# Stage 1 — Cheap market discovery

1. Call free `/events` to get Odds API event IDs.
2. Call slate-wide `totals` only.
3. Match full-game totals to AITA events.
4. Compare market full total to Monte Carlo fair-total distribution.
5. Calculate preliminary full-total EV.
6. Calculate **derivative-interest scores** for team totals and 1H totals from model outputs even though those sportsbook prices have not yet been pulled.

Cost can be approximately:

```text
1 credit per full slate totals snapshot
```

# Stage 2 — Expensive derivative scan only on shortlisted events

Only query:

```text
team_totals,totals_h1
```

for events that satisfy shortlist logic.

Possible shortlist triggers:

```text
high model-vs-market total disagreement
extreme team scoring asymmetry
strong offense-defense mismatch
high confidence score
large first-half vs full-game structural difference
large talent mismatch with stable first-half projection
low roster uncertainty
```

The shortlist should have a configurable hard maximum:

```text
MAX_DERIVATIVE_EVENTS_PER_RUN = 8 to 15
```

Do not let the model spend API credits because the slate is large.

---

# 13. Suggested free-plan quota policy

## Monthly quota

```text
500 credits
```

## Risk reserve

Keep at least:

```text
100-125 credits
```

uncommitted for:

- close capture
- retries
- postponed games
- rescheduled games
- special slates
- API schema diagnostics

## Operating budget

Target:

```text
<= 375-400 normal-use credits/month
```

## Weekly target

During a four-week month:

```text
~80-90 credits/week maximum normal operations
```

### Example weekly budget

Assume 12 derivative-shortlisted games.

```text
Tuesday/early snapshot:
  full totals slate = 1

Friday/Saturday decision snapshot:
  full totals slate = 1
  12 events × 2 derivative markets = 24

Close capture:
  full totals slate = 1
  12 events × 2 derivative markets = 24

Total ≈ 51 credits/week
```

Four weeks:

```text
~204 credits/month
```

This is comfortably within the 500-credit plan and leaves substantial reserve.

Even with 15 shortlisted games and two derivative snapshots:

```text
15 × 2 × 2 = 60 derivative credits
+ a few slate totals calls
```

still remains manageable if requests are disciplined.

---

# 14. If the account literally has 0 credits remaining

The pipeline must fail closed.

```text
IF x-requests-remaining <= configured_minimum:
    DISABLE_CHARGED_ODDS_CALLS
```

It may continue to:

- ingest ESPN data,
- ingest CFBD within its own quota,
- simulate games,
- generate fair lines,
- use locally cached odds,
- produce a `MARKET_DATA_UNAVAILABLE` board.

It must **not** fabricate current odds.

---

# 15. Odds API quota telemetry

After every Odds API response, save:

```text
x-requests-remaining
x-requests-used
x-requests-last
```

Create:

```text
ODDS_API_USAGE_LEDGER.csv
```

Fields:

```text
timestamp
endpoint
sport
markets
regions/bookmakers
event_id
cost_last
credits_used
credits_remaining
run_id
```

Before every charged call, compute projected cost and reject the call if it violates the run/week/month budget.

---

# 16. Bookmaker policy

V1 should use one U.S. bookmaker group/region and a preferred sportsbook whitelist.

Example configured targets may include books such as:

```text
DraftKings
FanDuel
BetMGM
Caesars
BetRivers
```

but the coding agent must validate the actual provider keys returned by The Odds API rather than assuming labels.

## 16.1 Do not expand regions casually

Because cost multiplies by region, V1 should not query:

```text
us + us2 + uk + eu
```

just to get more books.

A second region must have a demonstrated EV/coverage benefit before being enabled.

---

# 17. Closing-line capture without paid historical Odds API

This is critical.

The free Odds API plan does not provide historical odds access. Therefore AITA must build its own timestamped line history **prospectively**.

For each selected market, save:

```text
OPEN
MODEL_ENTRY
FINAL_PRE_KICK
```

or the nearest available snapshots.

## 17.1 Suggested definitions

### OPEN_PROXY
First AITA snapshot observed after the market becomes available.

### ENTRY
The exact snapshot used to generate the trading board.

### CLOSE_PROXY_PUBLIC
The final snapshot AITA captured before kickoff.

Do not label a snapshot “true close” unless the capture policy actually supports that claim.

## 17.2 Close-capture priority

Because derivative market calls are expensive, capture closes only for:

1. executed plays,
2. top-ranked EV candidates,
3. a small control sample of passes/watchlist bets.

This is enough to audit whether ranking quality predicts CLV without wasting quota on every derivative market in every game.

---

# 18. Market normalization

Every sportsbook outcome must normalize to:

```text
aita_event_id
market_family
period
team_if_applicable
side
over_under
point
american_price
bookmaker
last_update
snapshot_time
```

Canonical market families:

```text
FG_TOTAL
HOME_TEAM_TOTAL
AWAY_TEAM_TOTAL
H1_TOTAL
```

The model should never compare two offers unless the canonical market identity matches exactly.

---

# 19. Vig removal and market priors

For each two-sided over/under market:

1. convert American price to raw implied probability,
2. compute overround,
3. normalize to vig-free market probabilities.

Store:

```text
p_over_raw
p_under_raw
vig
p_over_fair_market
p_under_fair_market
```

The market-aware challenger uses the vig-free probability, not the raw implied probability.

---

# 20. Five required probability fields per candidate

Every candidate must output:

```text
P_MC
P_MARKET_FAIR
P_BLEND
P_CONSERVATIVE
P_BREAK_EVEN
```

## Definitions

### P_MC
Pure Monte Carlo probability from the football model.

### P_MARKET_FAIR
Vig-free sportsbook/consensus probability.

### P_BLEND
Market-aware calibrated probability.

### P_CONSERVATIVE
Probability after uncertainty shrinkage/lower-bound logic.

### P_BREAK_EVEN
Probability required to break even at the exact offered price.

---

# 21. Pure model vs market-aware model

Maintain two distinct model families.

## Pure

```text
p_pure = football model only
```

The sportsbook total may not enter as a predictor.

## Market-aware challenger

```text
p_blend = w * p_pure + (1-w) * p_market_fair
```

`w` should depend on:

```text
week
sample size
team uncertainty
model calibration history
market family
CLV history
roster stability
```

Week 0/1 should generally shrink more strongly toward market information than mature midseason states, unless evidence later disproves that policy.

---

# 22. EV engine

For American odds converted to payout `b`:

```text
EV_per_dollar = p_true * b - (1 - p_true)
EV_percent = 100 * EV_per_dollar
```

Calculate at least:

```text
EV_RAW
EV_BLEND
EV_CONSERVATIVE
```

The trade gate should be based primarily on conservative/blended EV, not raw Monte Carlo EV alone.

---

# 23. Confidence engine

Create a 0-100 confidence score from:

```text
data_quality
roster_certainty
qb_certainty
sample_size
model_agreement
simulation_convergence
market_agreement
historical_calibration
weather_certainty
entity_resolution_quality
```

Suggested bands:

```text
90-100 ELITE
80-89  HIGH
70-79  TRADABLE
60-69  WATCH
<60    PASS
```

Confidence is not EV. It is trust in the estimated EV.

---

# 24. Early-season mode

Weeks 0-3 require explicit protection against false precision.

```text
EARLY_SEASON_MODE = TRUE
```

Effects:

- larger latent sigmas
- stronger shrinkage
- greater prior-season weighting
- greater roster/QB continuity weighting
- reduced weight on tiny 2026 samples
- higher trade thresholds
- tighter maximum confidence unless roster information is strong
- optional smaller suggested stake tier

Transition out of early-season mode should be based on sample quality, not merely week number.

---

# 25. Full-game totals pricing

From Monte Carlo final scores:

```text
TOTAL_s = HOME_POINTS_s + AWAY_POINTS_s
```

Generate a full fair line curve.

For each candidate line `L`:

```text
P_OVER(L)
P_UNDER(L)
P_PUSH(L) if integer
```

Store the fair price for every relevant line.

---

# 26. Team totals pricing

From the same simulations:

```text
HOME_POINTS_s
AWAY_POINTS_s
```

Generate separate distributions.

This enables:

```text
P(home > line)
P(home < line)
P(away > line)
P(away < line)
```

The team-total engine must account for asymmetric blowout behavior.

---

# 27. First-half totals pricing

Do not use:

```text
H1 = 0.5 * full game
```

The simulation must store halftime state from the sequential possession process.

Generate:

```text
H1_HOME_POINTS_s
H1_AWAY_POINTS_s
H1_TOTAL_s
```

Then price the complete H1 total curve.

---

# 28. Cross-market consistency checks

The same Monte Carlo paths create all three markets, so contradictions should be detectable.

Examples of diagnostic flags:

```text
CROSS_MARKET_CONFLICT
TEAM_TOTAL_INCONSISTENCY
H1_FULL_GAME_INCONSISTENCY
MODEL_DISTRIBUTION_ANOMALY
```

Do not automatically assume every apparent conflict is impossible; vig and different lines matter. But extreme contradictions require review.

---

# 29. Correlation engine

Because every simulation generates every market outcome, calculate empirical correlation between candidate bet indicators.

Examples:

```text
Corr(FG_OVER, HOME_TT_OVER)
Corr(FG_OVER, AWAY_TT_OVER)
Corr(FG_OVER, H1_OVER)
Corr(HOME_TT_OVER, H1_OVER)
```

This is critical for portfolio risk.

A trading agent should not treat three highly correlated +EV positions as three independent bets.

---

# 30. Edge-driver explanation layer

For every top candidate, produce structured reasons.

Example fields:

```text
edge_driver_1
edge_driver_2
edge_driver_3
risk_driver_1
risk_driver_2
```

Possible drivers:

```text
pace advantage
offense-defense EPA mismatch
pass explosive mismatch
rush explosive mismatch
red-zone mismatch
QB continuity
OL continuity
opponent defensive weakness
first-half starter advantage
weather tail
blowout substitution risk
```

The explanation layer must be generated from actual feature deltas, not generic narrative templates.

---

# 31. Data-quality and fail-closed rules

A true risk-room system must know when not to price.

Create hard flags:

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

Each flag should have a severity:

```text
INFO
WARN
BLOCK
```

A `BLOCK` flag prevents an AITA ELITE classification.

---

# 32. Schema-drift tests

Because ESPN endpoints are unofficial, every ingestion run should validate required fields.

Examples:

```text
scoreboard contains events
competition has competitors
competitor has team identity
summary maps to expected event
roster entries have athlete identity
```

If required schema changes:

```text
SCHEMA_DRIFT = TRUE
```

and the system should preserve the raw payload for debugging.

---

# 33. Caching policy

## Immutable/historical

Cache permanently:

```text
completed game summaries
historical PBP
prior-season statistics
historical recruiting snapshots used by a model version
```

## Slowly changing

Refresh weekly:

```text
rosters
team metadata
rankings
season-to-date ratings
```

## Fast changing

Timestamp every pull:

```text
odds
weather
availability/injury-related information
```

The pipeline must never make an API call simply because the script restarted.

---

# 34. Suggested source-budget strategy by provider

## ESPN

Use aggressively but respectfully with caching and request throttling because it is not a guaranteed public developer API.

## CFBD

Free tier currently around 1,000 calls/month. Use broad/batched queries where possible and cache historical results permanently.

Recommended budget:

```text
preseason warehouse build: concentrated one-time calls
weekly update: small number of season/week filtered calls
historical data: never re-download unnecessarily
```

## The Odds API

Treat as scarce capital.

No polling loops.
No “refresh every minute.”
No querying markets outside V1.
No second region without explicit reason.

## Weather

Use a low/no-cost provider and cache by stadium + forecast run.

---

# 35. Weekly operational schedule

## Sunday night / Monday — postmortem

1. ingest final ESPN game data
2. ingest/store PBP/box scores
3. grade previous boards
4. calculate CLV from locally captured closing proxies
5. update calibration tables
6. update team/player feature store

## Tuesday — initial next-week build

1. discover next slate
2. refresh roster deltas
3. calculate preseason/current blended team states
4. run pure Monte Carlo
5. make one cheap slate-wide `totals` odds pull if useful
6. build preliminary watchlist

## Thursday/Friday — information refresh

1. refresh affected rosters/availability
2. refresh weather
3. refresh current-season metrics
4. rerun Monte Carlo only where inputs changed materially
5. reprioritize derivative shortlist

## Friday night / Saturday morning — trading-board run

1. fetch slate-wide full totals
2. select derivative shortlist
3. query `team_totals,totals_h1` only for shortlisted events
4. calculate exact EV at best available prices
5. run correlation/risk checks
6. produce final boards + ZIP

## Pre-kick close capture

For executed/top candidates only:

1. capture final full total slate
2. capture event derivative prices for selected candidates
3. timestamp as close proxy
4. never overwrite entry snapshot

---

# 36. Model-training and backtest discipline

The pipeline must prevent lookahead.

For any historical model state:

```text
feature_available_at <= decision_timestamp
```

Do not use:

- final-season ratings to predict early weeks
- roster information learned later
- closing lines as a predictor of an earlier pure model
- future injuries/results

Use walk-forward validation.

Example:

```text
train through 2023 → validate 2024
train through 2024 → validate 2025
lock 2026 deployment version
```

Then recalibrate carefully with 2026 live evidence.

---

# 37. Calibration scorecard

Track by market family:

```text
Brier score
log loss
calibration slope/intercept
ROI
CLV
average EV
EV-to-ROI realization
maximum drawdown
bet count
```

And by EV bucket:

```text
0-2%
2-4%
4-6%
6-10%
10%+
```

The critical test is whether higher predicted EV produces better CLV and eventually better realized ROI.

---

# 38. Three-market competition

Keep separate live ledgers for:

```text
FG_TOTAL
TEAM_TOTAL
H1_TOTAL
```

Do not assume all three remain five-star forever.

At defined sample thresholds, compute a market-quality score using:

```text
CLV
ROI
calibration
EV realization
drawdown
sample size
```

Then allow future capital/risk limits to favor the best-performing market family.

---

# 39. Trading-agent ZIP contract

The Python pipeline must emit one deterministic ZIP package.

Example:

```text
NCAAF_MONTE_TOTALS_2026_W01.zip

01_MANIFEST.json
02_NCAAF_FINAL_BOARDS.md
03_SLATE_EVENTS.csv
04_GAME_PROJECTIONS.csv
05_MONTE_CARLO_GAME_DISTRIBUTIONS.csv
06_FULL_GAME_TOTALS_BOARD.csv
07_TEAM_TOTALS_BOARD.csv
08_FIRST_HALF_TOTALS_BOARD.csv
09_MASTER_EV_BOARD.csv
10_MARKET_SNAPSHOT.csv
11_MODEL_CONFIDENCE.csv
12_EDGE_DRIVERS.csv
13_CORRELATION_MATRIX.csv
14_RISK_BOARD.csv
15_MC_CONVERGENCE_REPORT.csv
16_ODDS_API_USAGE_LEDGER.csv
17_DATA_QUALITY_REPORT.csv
18_MODEL_CARD.json
```

---

# 40. MANIFEST requirements

`01_MANIFEST.json` should declare:

```text
run_id
season
week
as_of_timestamp
model_version
feature_version
simulation_seed
simulation_count
early_season_mode
data_sources
raw_snapshot_ids
odds_snapshot_id
weather_snapshot_id
API_quota_remaining
files_in_zip
hashes
```

This allows the trading agent to know exactly what it received.

---

# 41. Final board requirements

## Board A — Full-game totals

```text
Rank
Matchup
Book total
Best price
Model mean total
Model median total
P_MC
P_BLEND
P_CONSERVATIVE
Fair price
EV_RAW
EV_BLEND
EV_CONSERVATIVE
Confidence
Grade
```

## Board B — Team totals

```text
Rank
Team
Market line
Best price
Model points mean/median
Over probability
Under probability
EV best side
Conservative EV
Confidence
Grade
```

## Board C — 1H totals

Same structure using the actual first-half simulation distribution.

## Board D — Master EV board

Rank all markets together after risk adjustment.

---

# 42. Grade taxonomy

A five-star **market family** does not mean every play is five-star.

Suggested trade classifications:

```text
AITA ELITE
AITA VALUE
WATCH
PASS
ENTERTAINMENT
```

Possible ELITE gates:

- positive conservative EV
- adequate model/market edge
- confidence above configured threshold
- no blocking data flags
- simulation converged
- market price fresh
- liquidity/book coverage acceptable
- correlation exposure acceptable

---

# 43. Risk-board requirements

The pipeline should calculate—not necessarily execute—risk metadata:

```text
recommended fractional Kelly input
max stake tier
same-game exposure
team exposure
market-family exposure
correlation cluster
API/data confidence
```

The downstream trading agent decides final execution.

---

# 44. Source of truth responsibilities

The coding agent should implement this hierarchy:

## Game identity and final result

Primary: ESPN  
Cross-check: CFBD where available

## Rosters / ESPN athlete identity

Primary: ESPN

## Advanced college-football analytics

Primary: CFBD or AITA-derived PBP metrics  
Cross-check: alternate calculation

## Market prices

Primary: The Odds API current snapshots  
Never use ESPN embedded odds as the authoritative trading price.

## Weather

Primary: dedicated weather API

## Closing line

Primary: AITA's own final pre-kick Odds API snapshot on free plan  
Label as close proxy unless proven to be exact market close.

---

# 45. Secret management

Never commit API keys.

Environment variables:

```text
ODDS_API_KEY
CFBD_API_KEY
```

ESPN generally does not require an API key for the endpoint families being used, but requests must still be throttled/cached.

`*.env` and secret files must be in `.gitignore`.

---

# 46. Reproducibility

Every Monte Carlo run should support a fixed random seed.

Persist:

```text
seed
simulation_count
model_version
feature_snapshot_id
```

Re-running the same package should reproduce the same probabilities within deterministic numerical behavior.

---

# 47. Minimum viable build order for the coding agent

## Milestone 1 — Data spine

- ESPN slate discovery
- ESPN team registry
- ESPN roster ingestion
- ESPN game-summary ingestion
- entity registry
- local caching/raw snapshots

## Milestone 2 — CFBD quant enrichment

- games/PBP
- advanced metrics
- ratings/recruiting as configured
- feature normalization

## Milestone 3 — Historical feature store

- offense/defense
- tempo
- possessions
- drives
- explosive plays
- turnovers
- player/QB continuity

## Milestone 4 — Monte Carlo V1

- latent team strength distributions
- possessions
- drive outcome engine
- halftime snapshot
- final score distribution
- convergence testing

## Milestone 5 — Market pricing

- full-game total curves
- home/away team total curves
- H1 total curves
- fair prices

## Milestone 6 — Odds API cost-aware adapter

- free events discovery
- slate totals call
- derivative shortlist
- event-level `team_totals,totals_h1`
- quota ledger
- cached market snapshots

## Milestone 7 — EV/risk

- vig removal
- P_MC / P_MARKET / P_BLEND / P_CONSERVATIVE / P_BE
- raw/blended/conservative EV
- confidence
- correlation
- grades

## Milestone 8 — ZIP handoff

- boards
- manifests
- model card
- usage ledger
- data-quality report

## Milestone 9 — Audit loop

- result grading
- close proxy capture
- CLV
- ROI
- calibration
- EV-bucket analysis

---

# 48. Non-negotiable coding rules

1. **No sportsbook line enters the pure football model.**
2. **No current odds are fabricated when API data is unavailable.**
3. **No ESPN response is treated as permanently stable; use adapters and schema tests.**
4. **No repeated historical API downloads when a valid local snapshot exists.**
5. **No Odds API polling loop.**
6. **No Odds API markets outside the approved V1 list by default.**
7. **No event-level derivative calls until the model shortlist exists.**
8. **No overwriting entry/close market snapshots.**
9. **No EV without exact price and exact break-even probability.**
10. **No ELITE label when conservative EV is negative or a blocking data-quality flag exists.**
11. **No first-half total derived mechanically as half of the full-game total.**
12. **No claim of “true close” from a manually timed snapshot; label close proxy accurately.**
13. **Every model and feature definition is versioned.**
14. **Every production run is reproducible.**
15. **Every external API call is logged.**

---

# 49. Recommended cost-aware request pattern

The coding agent should implement the weekly run approximately as follows:

```text
1. ESPN scoreboard → build slate
2. Odds API /events → map odds event IDs (free)
3. Load cached roster/team/history
4. Refresh only changed roster/current-week data
5. Pull/update CFBD quant inputs using batched historical/week requests
6. Pull weather
7. Run pure Monte Carlo for entire slate
8. Produce fair total/team-total/H1 curves for entire slate
9. Odds API full-game totals slate pull (1 market × 1 region)
10. Calculate preliminary FG total EV and derivative-interest scores
11. Rank games for derivative scan
12. Enforce API budget
13. Event-level Odds API pull for `team_totals,totals_h1` on top K games only
14. Calculate exact market EV
15. Blend/shrink probability
16. Calculate conservative EV
17. Calculate confidence and correlation
18. Generate boards
19. Generate ZIP
20. Later capture close proxies only for plays/top controls
21. After games, ingest final ESPN results and run audit
```

This is the “concert” architecture: each data source enters at the correct movement, not all at once.

---

# 50. Professional risk-room interpretation

The model is not built to say:

> “We think the Over wins.”

It is built to say:

```text
Our football model estimates a full scoring distribution.
At this exact sportsbook line and price, the probability required to break even is X.
Our pure probability is Y.
Our market-aware probability is Z.
Our conservative probability remains above break-even by N percentage points.
The resulting conservative EV is +E%.
The data quality is A.
The probability has converged.
The bet's correlation with existing exposure is C.
Therefore the position is ELITE / VALUE / WATCH / PASS.
```

That is the standard the coding agent should design around.

---

# 51. Current-source reference notes for the coding agent

These references should be rechecked during implementation because APIs, quotas and schemas can change.

## ESPN endpoint references

- ESPN endpoint catalog/community documentation:  
  https://github.com/sejaldua/espn-api/blob/main/references/endpoints.md
- ESPN hidden endpoint reference:  
  https://gist.github.com/akeaswaran/b48b02f1c94f873c6655e7129910fc3b

**Important:** ESPN endpoint documentation above is community documentation; treat ESPN JSON endpoints as unofficial and schema-test them.

## The Odds API

- NCAAF:  
  https://the-odds-api.com/sports/ncaaf-odds.html
- V4 docs:  
  https://the-odds-api.com/liveapi/guides/v4/
- Market keys:  
  https://the-odds-api.com/sports-odds-data/betting-markets.html
- Pricing/free credits:  
  https://the-odds-api.com/

## CollegeFootballData

- API docs:  
  https://api.collegefootballdata.com/
- Access tiers:  
  https://collegefootballdata.com/api-tiers
- Play-by-play:  
  https://api.collegefootballdata.com/api/plays
- Ratings:  
  https://api.collegefootballdata.com/api/ratings

## Weather

- Open-Meteo:  
  https://open-meteo.com/

---

# 52. Final build mandate

Build **one coherent NCAAF scoring-distribution system**, not three disconnected prediction scripts.

The production hierarchy is:

```text
ESPN + CFBD + WEATHER
        ↓
AITA NORMALIZED FOOTBALL STATE
        ↓
POSSESSION / DRIVE / GAME-STATE ENGINE
        ↓
MONTE CARLO FULL GAME
        ↓
FG TOTAL + TEAM TOTAL + H1 TOTAL DISTRIBUTIONS
        ↓
CHEAP SLATE-WIDE ODDS DISCOVERY
        ↓
MODEL SHORTLIST
        ↓
SELECTIVE EVENT-LEVEL DERIVATIVE ODDS
        ↓
VIG-FREE MARKET PRIOR
        ↓
PURE / BLENDED / CONSERVATIVE PROBABILITY
        ↓
EV + CONFIDENCE + CORRELATION
        ↓
AITA TRADING BOARD
        ↓
ZIP HANDOFF
        ↓
ENTRY/CLOSE/RESULT AUDIT
        ↓
CLV + ROI + CALIBRATION
        ↓
NEXT MODEL VERSION
```

The central objective is not maximum number of bets. It is maximum **quality-adjusted, reproducible, auditable EV** while conserving scarce market-data credits and continuously proving the model against the closing market.

---

# 53. Definition of done for V1

The coding agent should not call V1 complete until all of the following are true:

- [ ] ESPN slate and team/event identities resolve reliably.
- [ ] Current and historical roster snapshots are cached.
- [ ] ESPN/CFBD data normalize into a single AITA schema.
- [ ] Historical completed games can be reconstructed without future leakage.
- [ ] Team offensive/defensive/tempo/drive features are generated.
- [ ] Early-season uncertainty is explicit.
- [ ] Monte Carlo produces halftime and final-score distributions.
- [ ] Simulation convergence is measured.
- [ ] Full-game total fair curves are generated.
- [ ] Home/away team-total fair curves are generated.
- [ ] 1H total fair curves are generated from actual halftime simulations.
- [ ] Odds API event discovery consumes zero quota where documented.
- [ ] Slate-wide totals pull is cost-aware.
- [ ] Event-level derivative queries only occur after shortlisting.
- [ ] Odds API usage headers are logged.
- [ ] Monthly/weekly quota guards are enforced.
- [ ] Entry and close-proxy snapshots are immutable.
- [ ] Vig-free probabilities are calculated correctly.
- [ ] Raw, blended and conservative EV are produced.
- [ ] Confidence and data-quality flags are produced.
- [ ] Cross-market correlation is estimated from Monte Carlo paths.
- [ ] Final ZIP contract is deterministic.
- [ ] Postgame result/CLV/ROI/calibration audit can feed the next weekly run.

**When these conditions are satisfied, AITA has a true NCAAF Monte Carlo totals pricing desk rather than a prediction script.**
