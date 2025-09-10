# trader/datasources/yfinance_source.py
import yfinance as yf
import pandas as pd
from pathlib import Path
from trader.config import RAW_DIR, DEFAULT_START
import warnings
warnings.simplefilter("ignore")

def _normalize_multi(df):
    if isinstance(df.columns, pd.MultiIndex):
        df = df.stack(level=-1)                     # (date, ticker) index
        df = df.rename_axis(index=["date", "symbol"]).reset_index()
        df.columns = [c.lower() if isinstance(c, str) else c for c in df.columns]
        return df
    return df

def fetch(symbols, start=DEFAULT_START, end=None, interval="1d", adjust=True):
    df = yf.download(
        symbols, start=start, end=end, interval=interval,
        auto_adjust=adjust, progress=False, group_by="column"
    )
    df = _normalize_multi(df)                       # MultiIndex -> long
    if "date" not in df.columns:                   # tek sembolde de tutarlı ol
        df = df.rename(columns=str.lower).reset_index()
    return df

def save_raw(df, name="prices"):
    Path(RAW_DIR).mkdir(parents=True, exist_ok=True)
    df.to_parquet(f"{RAW_DIR}/{name}.parquet")