import pandas as pd
from trader.features.indicators import cci

def compute_cci_signals(df, n=20, upper=100, lower=-100):
    c = cci(df, n)
    buy = (c.shift(1) < lower) & (c >= lower)
    sell = (c.shift(1) > upper) & (c <= upper)
    return c, buy.astype(int), sell.astype(int)