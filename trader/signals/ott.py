import pandas as pd
import numpy as np
from trader.features.indicators import ema, sma

def compute_ott(df: pd.DataFrame, length: int = 2, percent: float = 1.4, ma_type: str = "EMA") -> pd.Series:
    """OTT çizgisini hesaplar ve df'e 'ott' kolonunu ekler."""
    price = df["close"]

    # Basit MA seçimleri (şimdilik EMA/SMA)
    if ma_type.upper() == "SMA":
        mav = sma(price, length)
    else:
        mav = ema(price, length)

    fark = mav * percent * 0.01

    # Long/short stop hesapları
    long_stop = pd.Series(index=price.index, dtype="float64")
    short_stop = pd.Series(index=price.index, dtype="float64")

    for i in range(len(price)):
        ls = mav.iat[i] - fark.iat[i]
        ss = mav.iat[i] + fark.iat[i]
        if i == 0:
            long_stop.iat[i] = ls
            short_stop.iat[i] = ss
        else:
            long_stop.iat[i] = max(ls, long_stop.iat[i-1]) if mav.iat[i] > long_stop.iat[i-1] else ls
            short_stop.iat[i] = min(ss, short_stop.iat[i-1]) if mav.iat[i] < short_stop.iat[i-1] else ss

    # Yön (trend) belirleme
    dirv = pd.Series(1, index=price.index, dtype="int64")
    for i in range(1, len(price)):
        if dirv.iat[i-1] == -1 and mav.iat[i] > short_stop.iat[i-1]:
            dirv.iat[i] = 1
        elif dirv.iat[i-1] == 1 and mav.iat[i] < long_stop.iat[i-1]:
            dirv.iat[i] = -1
        else:
            dirv.iat[i] = dirv.iat[i-1]

    # OTT çizgisi
    mt = pd.Series(index=price.index, dtype="float64")
    mt[dirv == 1] = long_stop[dirv == 1]
    mt[dirv == -1] = short_stop[dirv == -1]

    ott_up = mt * (200 + percent) / 200
    ott_dn = mt * (200 - percent) / 200

    ott = pd.Series(index=price.index, dtype="float64")
    ott[mav > mt] = ott_up[mav > mt]
    ott[mav <= mt] = ott_dn[mav <= mt]

    df["ott"] = ott
    df["mavg"] = mav
    return df

def signals_price_vs_ott(df: pd.DataFrame):
    """Price vs OTT: fiyat OTT'yi yukarı kesince BUY, aşağı kesince SELL"""
    x = df["close"]
    o = df["ott"]
    buy = (x.shift(1) <= o.shift(1)) & (x > o)
    sell = (x.shift(1) >= o.shift(1)) & (x < o)
    return buy.astype(int), sell.astype(int)