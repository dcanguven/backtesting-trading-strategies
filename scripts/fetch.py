from trader.datasources.yfinance_source import fetch, save_raw

SYMS = ["AAPL", "MSFT", "SPY", "THYAO.IS", "ASELS.IS"]

if __name__ == "__main__":
    df = fetch(SYMS)
    save_raw(df, "prices")
    print(df.head())