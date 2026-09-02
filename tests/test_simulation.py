import numpy as np
from ncaaf_aita.features.state import TeamState
from ncaaf_aita.simulation.engine import MonteCarloEngine


def test_simulation_reproducible_and_has_halftime():
    h=TeamState("H",offense_ppd=3.0,defense_ppd_allowed=2.2,sample_size=3)
    a=TeamState("A",offense_ppd=2.4,defense_ppd_allowed=2.7,sample_size=3)
    x=MonteCarloEngine(42).simulate(h,a,5000)
    y=MonteCarloEngine(42).simulate(h,a,5000)
    assert np.array_equal(x.total,y.total)
    assert np.mean(x.h1_total)>0
    assert np.mean(x.total)>np.mean(x.h1_total)


def test_first_half_is_not_mechanical_half_score():
    h=TeamState("H",offense_ppd=3.1,defense_ppd_allowed=2.3,possessions_mean=13.0,first_half_possessions=7.2,sample_size=4)
    a=TeamState("A",offense_ppd=2.6,defense_ppd_allowed=2.8,possessions_mean=11.8,first_half_possessions=5.2,sample_size=4)
    x=MonteCarloEngine(7).simulate(h,a,10000)
    assert abs(np.mean(x.h1_total) - .5*np.mean(x.total)) > .05
