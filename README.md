# Backtesting Trading Strategies

<img width="2071" height="1115" alt="image" src="https://github.com/user-attachments/assets/1155b2e3-88c6-471c-b30c-92a7c688402d" />


Interactive Streamlit application for testing and comparing rule-based trading strategies on historical market data.

The application allows users to:

- test multiple technical indicator strategies
- combine signals using different decision modes
- compare strategy performance against Buy & Hold
- visualize BUY and SELL signals on charts
- explore parameter sensitivity
- rank model combinations

https://backtesting-trading-strategies.streamlit.app/

---

## Typical Workflow

A typical analysis flow looks like this:

1. Search a stock symbol
2. Set the initial capital
3. Choose the backtest start date
4. Select a combine mode
5. Configure trading fee assumptions
6. Select one or multiple technical models
7. Adjust indicator parameters
8. Analyze charts and KPIs
9. Compare strategies using the Model Performance table

---

### 1. Symbol Search

Enter the symbol you want to analyze.

Examples:

```txt
AAPL
NVDA
MSFT
TSLA
XU100.IS
```

After clicking Search:

- historical data is loaded
- charts are generated
- the backtest runs automatically
- model combinations are ranked


### 2. Initial Capital

Defines the starting portfolio size used in the backtest.

This affects:

- Strategy Value
- Equity chart scaling
- Buy & Hold Value

It does **not** change percentage returns.

### 3. Start Date

Defines when the backtest begins.

The application automatically uses **the latest available market data** as the end date.


### 4. Fee (bps)

Simulates transaction costs.

Examples:

| bps | Percentage |
|---|---|
| 1 | 0.01% |
| 10 | 0.10% |
| 20 | 0.20% |


### 5. Combine Modes

<img width="279" height="228" alt="image" src="https://github.com/user-attachments/assets/139cf607-4b9b-4a75-9491-82e3ccbbf91c" />


Combine Modes define how selected models generate BUY and SELL signals together.

| Mode | Behavior |
|---|---|
| NONE | Buy & Hold style |
| ANY | Any selected model can trigger signals |
| ALL | All selected models must agree |
| VOTE | A minimum number of models must agree |


#### NONE

Ignores technical signals and behaves similarly to Buy & Hold.

Useful as a baseline comparison.

#### ANY

If any selected model generates a BUY or SELL signal, the strategy reacts.

Results:

- more trades
- faster reactions
- more aggressive behavior


#### ALL

All selected models must agree before generating a signal.

Results:

- fewer trades
- stricter confirmation
- more selective entries

#### VOTE

A minimum number of selected models must agree before generating a signal.

At least 2 models must agree before BUY or SELL occurs.

Higher Vote k:

- fewer trades
- stricter confirmation

Lower Vote k:

- more trades
- more aggressive behavior


### 6. Selecting Models

The sidebar allows multiple models to be selected simultaneously.

Examples:

```txt
RSI + CCI
OTT + TMA
RSI + CCI + OTT + TMA
```

The selected models generate signals together according to the selected Combine Mode.


### 7. Indicator Parameters

Each indicator has adjustable parameters that change signal sensitivity and behavior.

#### RSI Parameters

Measures momentum strength.

| Parameter | Effect |
|---|---|
| RSI n | Higher values create smoother and slower signals |
| Overbought | Lower values trigger SELL signals earlier |
| Oversold | Higher values trigger BUY signals earlier |

Default values:

```txt
RSI n = 14
Overbought = 70
Oversold = 30
```

#### CCI Parameters

Measures price deviation from its average.

| Parameter | Effect |
|---|---|
| CCI n | Controls sensitivity |
| CCI upper | Higher values create fewer SELL signals |
| CCI lower | Lower values create fewer BUY signals |

Default values:

```txt
CCI n = 20
CCI upper = 100
CCI lower = -100
```

#### OTT Parameters

A trend-following indicator.

| Parameter | Effect |
|---|---|
| OTT length | Higher values react more slowly |
| OTT percent | Higher values create stricter signals |

Default values:

```txt
OTT length = 2
OTT percent = 1.4
```

#### TMA Parameters

Uses multiple EMA relationships to identify trends.

| Parameter | Effect |
|---|---|
| TMA fast | Short-term trend speed |
| TMA mid | Medium-term trend filter |
| TMA slow | Long-term trend filter |

Default values:

```txt
TMA fast = 5
TMA mid = 20
TMA slow = 50
```

### 8. Reading the Results

After running the backtest, the application displays charts and KPIs.

| KPI | Meaning |
|---|---|
| Strategy Return | Total percentage return |
| Strategy Value | Final portfolio value |
| Volatility | Return fluctuation level |
| Buys / Sells | Number of trading actions |

---

### 9. Price Chart

Displays historical prices and trading signals.

Features:

- green markers = BUY signals
- red markers = SELL signals
- highlighted areas = active positions
- interactive hover tooltip

---

### 10. Equity Chart

Shows portfolio value over time.


### 11. Capital Snapshot

Compares the active strategy against Buy & Hold.

Includes:

- Buy & Hold Return
- Buy & Hold Value

### 12. Model Performance Table

Ranks model combinations.

<img width="438" height="530" alt="image" src="https://github.com/user-attachments/assets/a104e4a0-4c2f-4522-a6ba-fe2dc75ab016" />


| Column | Meaning |
|---|---|
| Combo | Tested model combination |
| Mode | Signal combination method |
| Trades | Number of completed trades |
| TotalReturn(%) | Total strategy return |


---

## Important Disclaimer

This project is designed for educational and analytical purposes.

Backtest results:

- rely on historical data
- do not guarantee future performance
- cannot fully represent real market conditions
