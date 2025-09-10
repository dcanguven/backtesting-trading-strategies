import pandas as pd
import numpy as np

def combine(signals: dict, mode: str = "ANY", k: int | None = None, index: pd.Index | None = None):
    m = mode.upper()
    if m == "NONE":
        if index is None:
            raise ValueError("index is required for NONE mode")
        entry = pd.Series(0, index=index, dtype=int)
        exit_ = pd.Series(0, index=index, dtype=int)
        if len(index) > 0:
            entry.iat[0] = 1
        return entry, exit_
    b = pd.DataFrame({name: pair[0].astype(int) for name, pair in signals.items()})
    s = pd.DataFrame({name: pair[1].astype(int) for name, pair in signals.items()})
    if m == "ALL":
        entry = (b.sum(axis=1) == b.shape[1]).astype(int)
        exit_ = (s.sum(axis=1) == s.shape[1]).astype(int)
    elif m == "VOTE":
        th = k if k is not None else int(np.ceil(len(signals) / 2))
        entry = (b.sum(axis=1) >= th).astype(int)
        exit_ = (s.sum(axis=1) >= th).astype(int)
    else:
        entry = (b.sum(axis=1) >= 1).astype(int)
        exit_ = (s.sum(axis=1) >= 1).astype(int)
    return entry, exit_