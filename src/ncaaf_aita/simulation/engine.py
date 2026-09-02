from __future__ import annotations

from dataclasses import dataclass
import numpy as np

from ncaaf_aita.features.state import TeamState, WeatherState, weather_scoring_multiplier


@dataclass
class GameSimulationResult:
    home_points: np.ndarray
    away_points: np.ndarray
    h1_home_points: np.ndarray
    h1_away_points: np.ndarray
    home_possessions: np.ndarray
    away_possessions: np.ndarray
    seed: int

    @property
    def total(self): return self.home_points + self.away_points
    @property
    def h1_total(self): return self.h1_home_points + self.h1_away_points


class MonteCarloEngine:
    def __init__(self, seed: int = 20260901):
        self.seed = seed

    @staticmethod
    def _matchup_ppd(off: TeamState, deff: TeamState, latent_off: np.ndarray, latent_def: np.ndarray,
                     weather: WeatherState | None, home_adv: float) -> np.ndarray:
        base = np.sqrt(np.maximum(0.25, off.offense_ppd * deff.defense_ppd_allowed))
        weather_mult = weather_scoring_multiplier(weather, off.pass_rate)
        explosive_delta = np.clip(off.explosive_rate - deff.explosive_rate_allowed, -0.12, 0.12)
        rz_delta = np.clip(off.red_zone_td_rate - deff.def_red_zone_td_rate_allowed, -0.25, 0.25)
        pressure = np.clip((off.sack_rate_allowed + deff.sack_rate_created) - 0.12, -0.06, 0.10)
        success_delta = np.clip(off.success_rate - deff.def_success_rate_allowed, -0.15, 0.15)
        matchup_mult = (1.0 + 0.22*explosive_delta + 0.10*rz_delta + 0.12*success_delta - 0.45*pressure
                        + 0.04*off.special_teams_rating)
        return np.clip(base * latent_off * latent_def * weather_mult * home_adv * matchup_mult, 0.45, 5.7)

    @staticmethod
    def _drive_probs(ppd: np.ndarray, td_share: float, fg_share: float, turnover_rate: float,
                     explosive_rate: float, state_mult: np.ndarray):
        target = np.clip(ppd * state_mult, 0.35, 5.9)
        denom = max(td_share + (3/7)*fg_share, 1e-6)
        td_p = np.clip((target / 7.0) * td_share / denom, 0.02, 0.62)
        fg_p = np.clip((target - 7*td_p) / 3.0, 0.01, 0.34)
        return td_p, fg_p, np.clip(turnover_rate, 0.02, 0.28), np.clip(0.004 + 0.045*explosive_rate, 0.003, 0.025)

    def _segment(self, rng, hp, ap, h_n, a_n, h_ppd, a_ppd, home, away):
        max_drives = int(max(h_n.max(initial=0), a_n.max(initial=0)))
        for d in range(max_drives):
            margin = hp.astype(float) - ap.astype(float)
            h_state = np.where(margin <= -14, 1.06, np.where(margin >= 24, 0.84, np.where(margin >= 10, 0.94, 1.0)))
            a_state = np.where(margin >= 14, 1.06, np.where(margin <= -24, 0.84, np.where(margin <= -10, 0.94, 1.0)))
            for active, ppd, team, opp, state, points, opp_points in (
                (d < h_n, h_ppd, home, away, h_state, hp, ap),
                (d < a_n, a_ppd, away, home, a_state, ap, hp),
            ):
                idx = np.flatnonzero(active)
                if idx.size == 0: continue
                td_p, fg_p, to_p, dst_p = self._drive_probs(ppd[idx], team.td_share, team.fg_share, team.turnover_rate, team.explosive_rate, state[idx])
                u = rng.random(idx.size)
                score = np.zeros(idx.size, dtype=np.int16)
                score[u < td_p] = 7
                score[(u >= td_p) & (u < td_p + fg_p)] = 3
                defensive = (u >= td_p + fg_p) & (u < td_p + fg_p + to_p*dst_p)
                opp_points[idx[defensive]] += 7
                points[idx] += score

    def simulate(self, home: TeamState, away: TeamState, n: int, weather: WeatherState | None = None,
                 neutral_site: bool = False) -> GameSimulationResult:
        rng = np.random.default_rng(self.seed)
        early_unc = 1.0 + 0.30 * max(0.0, 0.6 - (home.roster_continuity + away.roster_continuity)/2)
        h_off = rng.lognormal(mean=-0.5*(home.offense_sigma*early_unc)**2, sigma=home.offense_sigma*early_unc, size=n)
        a_off = rng.lognormal(mean=-0.5*(away.offense_sigma*early_unc)**2, sigma=away.offense_sigma*early_unc, size=n)
        h_def = rng.lognormal(mean=-0.5*(away.defense_sigma*early_unc)**2, sigma=away.defense_sigma*early_unc, size=n)
        a_def = rng.lognormal(mean=-0.5*(home.defense_sigma*early_unc)**2, sigma=home.defense_sigma*early_unc, size=n)
        h_ppd = self._matchup_ppd(home, away, h_off, h_def, weather, 1.0 if neutral_site else 1.035)
        a_ppd = self._matchup_ppd(away, home, a_off, a_def, weather, 1.0)

        pace_mean = np.clip((home.possessions_mean + away.possessions_mean)/2, 8.5, 17.0)
        pace_sd = np.clip((home.possessions_sd + away.possessions_sd)/2, 0.8, 2.5)
        shared = rng.normal(pace_mean, pace_sd, size=n)
        h_poss = np.clip(np.rint(shared + rng.normal(0, 0.55, n)), 7, 19).astype(int)
        a_poss = np.clip(np.rint(shared + rng.normal(0, 0.55, n)), 7, 19).astype(int)

        # First-half possessions are modeled independently rather than mechanically halving full-game scores.
        h_h1_share = np.clip(home.first_half_possessions / max(home.possessions_mean, 1.0), 0.36, 0.62)
        a_h1_share = np.clip(away.first_half_possessions / max(away.possessions_mean, 1.0), 0.36, 0.62)
        h_h1 = np.clip(np.rint(h_poss*h_h1_share + rng.normal(0, 0.35, n)), 3, h_poss).astype(int)
        a_h1 = np.clip(np.rint(a_poss*a_h1_share + rng.normal(0, 0.35, n)), 3, a_poss).astype(int)

        hp = np.zeros(n, dtype=np.int16); ap = np.zeros(n, dtype=np.int16)
        self._segment(rng, hp, ap, h_h1, a_h1, h_ppd, a_ppd, home, away)
        h1hp = hp.copy(); h1ap = ap.copy()
        self._segment(rng, hp, ap, h_poss-h_h1, a_poss-a_h1, h_ppd, a_ppd, home, away)
        return GameSimulationResult(hp, ap, h1hp, h1ap, h_poss, a_poss, self.seed)
