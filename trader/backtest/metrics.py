import pandas as pd
import numpy as np

def metrics(eq: pd.Series, net: pd.Series, freq: int = 252):
    total_return = float(eq.iloc[-1] - 1.0) if len(eq) else 0.0
    cagr = float(eq.iloc[-1] ** (freq / max(len(eq), 1)) - 1.0) if len(eq) else 0.0
    maxdd = float((eq / eq.cummax() - 1.0).min()) if len(eq) else 0.0
    vol = float(net.std() * (freq ** 0.5)) if len(net) else 0.0
    days = int(len(eq))
    return {"TotalReturn": total_return, "CAGR": cagr, "MaxDD": maxdd, "Vol": vol, "Days": days}