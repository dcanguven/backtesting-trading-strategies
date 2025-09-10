import pandas as pd
from trader.features.indicators import ema, sma
import warnings
warnings.simplefilter("ignore", FutureWarning)

def _ma(s: pd.Series, n: int, kind: str = "EMA") -> pd.Series:
    if kind.upper() == "SMA":
        return sma(s, n)
    return ema(s, n)

def compute_tma_series(close: pd.Series, fast: int = 5, mid: int = 20, slow: int = 50, ma_type: str = "EMA"):
    mf = _ma(close, fast, ma_type)
    mm = _ma(close, mid, ma_type)
    ms = _ma(close, slow, ma_type)
    return mf, mm, ms

def signals_tma_order(mf: pd.Series, mm: pd.Series, ms: pd.Series):
    up = (mf > mm) & (mm > ms)
    dn = (mf < mm) & (mm < ms)
    buy = (~up.shift(1).fillna(False)) & up
    sell = (~dn.shift(1).fillna(False)) & dn
    return buy.astype(int), sell.astype(int)