from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from trader.datasources.yfinance_source import fetch, save_raw

SYMS = ["AAPL", "MSFT", "SPY", "THYAO.IS", "ASELS.IS"]

if __name__ == "__main__":
    df = fetch(SYMS)
    save_raw(df, "prices")
    print(df.head())
