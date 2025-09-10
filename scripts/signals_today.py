import sys
import pandas as pd
from trader.io.store import load_raw
from trader.signals.rsi import compute_rsi_signals
from trader.signals.cci import compute_cci_signals
from trader.signals.ott import compute_ott, signals_price_vs_ott
from trader.signals.tma import compute_tma_series, signals_tma_order
import warnings
warnings.simplefilter("ignore")

SYMBOL = "AAPL"

def main(symbol: str = SYMBOL):
    df_all = load_raw()
    if df_all.empty or "symbol" not in df_all.columns:
        sys.exit(1)
    df = (
        df_all[df_all["symbol"] == symbol]
        .sort_values("date")
        .reset_index(drop=True)
        .copy()
    )
    if df.empty:
        sys.exit(1)
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    r, rb, rs = compute_rsi_signals(df["close"], n=14, ob=70, os=30)
    c, cb, cs = compute_cci_signals(df, n=20, upper=100, lower=-100)
    df = compute_ott(df, length=2, percent=1.4, ma_type="EMA")
    ob, os = signals_price_vs_ott(df)
    mf, mm, ms = compute_tma_series(df["close"], fast=5, mid=20, slow=50, ma_type="EMA")
    tb, ts = signals_tma_order(mf, mm, ms)
    out = pd.DataFrame({
        "date": df["date"],
        "close": df["close"],
        "rsi": r.round(2),
        "rsi_buy": rb,
        "rsi_sell": rs,
        "cci": c.round(2),
        "cci_buy": cb,
        "cci_sell": cs,
        "ott": df["ott"].round(4),
        "ott_buy": ob,
        "ott_sell": os,
        "tma_buy": tb,
        "tma_sell": ts
    })
    print(out.tail(5))
    print("\nTODAY:")
    print(out.iloc[-1][[
        "date","close",
        "rsi","rsi_buy","rsi_sell",
        "cci","cci_buy","cci_sell",
        "ott","ott_buy","ott_sell",
        "tma_buy","tma_sell"
    ]])

if __name__ == "__main__":
    main()