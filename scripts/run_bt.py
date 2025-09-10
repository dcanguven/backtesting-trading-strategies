import sys
import pandas as pd
from trader.io.store import load_raw
from trader.signals.rsi import compute_rsi_signals
from trader.signals.cci import compute_cci_signals
from trader.signals.ott import compute_ott, signals_price_vs_ott
from trader.signals.tma import compute_tma_series, signals_tma_order
from trader.signals.combine import combine
from trader.backtest.engine import backtest_long_only
from trader.backtest.metrics import metrics

SYMBOL = "AAPL"

def main(symbol: str = SYMBOL, mode: str = "VOTE", k: int | None = 2, fee_bps: int = 10, slip_bps: int = 0):
    df_all = load_raw()
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

    signals = {"ott": (ob, os), "tma": (tb, ts), "cci": (cb, cs), "rsi": (rb, rs)}
    entry, exit_ = combine(signals, mode=mode, k=k)

    eq, net, pos = backtest_long_only(df, entry, exit_, fee_bps=fee_bps, slip_bps=slip_bps)
    m = metrics(eq, net)
    print(pd.Series(m).round(4))
    print(eq.tail(5))

if __name__ == "__main__":
    main()