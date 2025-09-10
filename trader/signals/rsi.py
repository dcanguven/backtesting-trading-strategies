import pandas as pd
from trader.features.indicators import rsi

def compute_rsi_signals(close, n=14, ob=70, os=30):
    r = rsi(close, n)
    buy = (r.shift(1) < os) & (r >= os)
    sell = (r.shift(1) > ob) & (r <= ob)
    return r, buy.astype(int), sell.astype(int)