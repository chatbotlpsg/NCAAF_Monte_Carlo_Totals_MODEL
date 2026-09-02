from __future__ import annotations

import numpy as np
import pandas as pd


def indicator_correlation(indicators: dict[str, np.ndarray]) -> pd.DataFrame:
    names = list(indicators)
    if not names:
        return pd.DataFrame()
    arr = np.vstack([np.asarray(indicators[n], dtype=float) for n in names])
    corr = np.corrcoef(arr)
    corr = np.nan_to_num(corr, nan=0.0)
    return pd.DataFrame(corr, index=names, columns=names)
