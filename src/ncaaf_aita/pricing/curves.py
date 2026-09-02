from __future__ import annotations

import numpy as np
import pandas as pd
from ncaaf_aita.pricing.odds_math import probability_to_american


def prob_at_line(values: np.ndarray, line: float, side: str) -> tuple[float, float]:
    side = side.upper()
    if side == "OVER":
        win = float(np.mean(values > line)); push = float(np.mean(values == line))
    else:
        win = float(np.mean(values < line)); push = float(np.mean(values == line))
    return win, push


def curve(values: np.ndarray, lines: np.ndarray, label: str) -> pd.DataFrame:
    rows = []
    for line in lines:
        po = float(np.mean(values > line)); pu = float(np.mean(values < line)); pp = float(np.mean(values == line))
        rows.append({"market": label, "line": float(line), "p_over": po, "p_under": pu, "p_push": pp,
                     "fair_over_american": probability_to_american(po/max(1e-12, 1-pp)),
                     "fair_under_american": probability_to_american(pu/max(1e-12, 1-pp))})
    return pd.DataFrame(rows)
