from ncaaf_aita.pricing.odds_math import american_to_break_even, vig_free_two_way
from ncaaf_aita.ev.engine import ev_percent, ev_percent_with_push


def test_break_even_minus_219():
    assert abs(american_to_break_even(-219)-0.68652) < 1e-4


def test_ev_example_minus_219():
    assert abs(ev_percent(.846,-219)-23.27) < .05


def test_vig_free_minus_110():
    o,u,v=vig_free_two_way(-110,-110)
    assert abs(o-.5)<1e-12 and abs(u-.5)<1e-12 and v>0


def test_push_adjusted_ev():
    base = ev_percent(.55, -110)
    assert abs(ev_percent_with_push(.55, -110, .05) - .95*base) < 1e-12
