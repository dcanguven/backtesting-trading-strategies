import pandas as pd

def backtest_long_only(df: pd.DataFrame, entry: pd.Series, exit_: pd.Series, fee_bps: int = 10, slip_bps: int = 0):
    price = df["close"]
    ret = price.pct_change().fillna(0.0)
    pos = pd.Series(0, index=df.index, dtype="int64")
    entries = 0
    exits = 0
    for i in range(1, len(df)):
        if exit_.iat[i] == 1 and pos.iat[i - 1] == 1:
            pos.iat[i] = 0
            exits += 1
        elif entry.iat[i] == 1 and pos.iat[i - 1] == 0:
            pos.iat[i] = 1
            entries += 1
        else:
            pos.iat[i] = pos.iat[i - 1]
    fees = (fee_bps + slip_bps) / 10000.0
    traded = ((entry == 1) | (exit_ == 1)).astype(int)
    net = pos.shift(1).fillna(0) * ret - traded * fees
    eq = (1.0 + net).cumprod()
    trades = int(min(entries, exits))
    open_trades = int(max(entries - exits, 0))
    return eq, net, pos, trades, entries, exits, open_trades