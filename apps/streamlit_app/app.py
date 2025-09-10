import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import pandas as pd
import streamlit as st
import altair as alt
from datetime import date
from itertools import combinations

from trader.io.store import load_raw
from trader.signals.rsi import compute_rsi_signals
from trader.signals.cci import compute_cci_signals
from trader.signals.ott import compute_ott, signals_price_vs_ott
from trader.signals.tma import compute_tma_series, signals_tma_order
from trader.signals.combine import combine
from trader.backtest.engine import backtest_long_only
from trader.backtest.metrics import metrics
from trader.datasources.yfinance_source import fetch
import warnings
warnings.simplefilter("ignore")


st.set_page_config(page_title="Signals & Backtest", layout="wide")
st.title("Backtesting Trading Strategies")

st.markdown("""
<style>
[data-testid="stMetricValue"] {
    font-size: 1.35rem !important;  /* 1.3–1.4 iyi bir orta yol */
    line-height: 1.3 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.9rem !important;   /* 0.9–1.0 okunaklı kalır */
    line-height: 1.2 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
.header-label { font-size: 0.82rem; color: #9aa0a6; margin-bottom: 0.25rem; }
</style>
""", unsafe_allow_html=True)

RAW_PATH = "data/raw/prices.parquet"

def symbol_meta(symbol: str):
    s = symbol.upper()
    mapping = {
        ".IS": ("Borsa Istanbul (Turkey)", "TRY"),
        ".TO": ("Toronto (Canada)", "CAD"),
        ".V":  ("TSX Venture (Canada)", "CAD"),
        ".L":  ("London (UK)", "GBP"),
        ".DE": ("Xetra (Germany)", "EUR"),
        ".PA": ("Euronext Paris (France)", "EUR"),
        ".MI": ("Borsa Italiana (Italy)", "EUR"),
        ".AS": ("Euronext Amsterdam (Netherlands)", "EUR"),
        ".HK": ("Hong Kong", "HKD"),
        ".T":  ("Tokyo (Japan)", "JPY"),
        ".KS": ("Korea Exchange", "KRW"),
        ".KQ": ("KOSDAQ (Korea)", "KRW"),
        ".AX": ("ASX (Australia)", "AUD"),
        ".NZ": ("NZX (New Zealand)", "NZD"),
        ".SG": ("SGX (Singapore)", "SGD"),
        ".SW": ("SIX (Switzerland)", "CHF"),
        ".ZU": ("SIX (Switzerland)", "CHF"),
        ".BM": ("BME (Spain)", "EUR"),
        ".OL": ("Oslo (Norway)", "NOK"),
        ".ST": ("Stockholm (Sweden)", "SEK"),
        ".HE": ("Helsinki (Finland)", "EUR"),
        ".CO": ("Copenhagen (Denmark)", "DKK"),
        ".BK": ("SET (Thailand)", "THB"),
        ".JK": ("IDX (Indonesia)", "IDR"),
        ".TW": ("TWSE (Taiwan)", "TWD"),
        ".TA": ("TASE (Israel)", "ILS"),
    }
    for suf, meta in mapping.items():
        if s.endswith(suf):
            return meta
    return ("US (NYSE/Nasdaq)", "USD")

def load_data():
    df = load_raw().copy()
    if not pd.api.types.is_datetime64_any_dtype(df["date"]):
        df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["symbol", "date"]).reset_index(drop=True)
    return df

def fetch_and_append(yf_symbol: str, start_date: str):
    df_old = load_raw()
    df_new = fetch([yf_symbol], start=start_date, interval="1d", adjust=True)
    if df_new.empty:
        return False
    df_all = pd.concat([df_old, df_new], ignore_index=True)
    df_all = df_all.drop_duplicates(subset=["date", "symbol"]).sort_values(["symbol", "date"]).reset_index(drop=True)
    df_all.to_parquet(RAW_PATH)
    return True

def build_signals(df: pd.DataFrame, rsi_n=14, rsi_ob=70, rsi_os=30,
                  cci_n=20, cci_up=100, cci_lo=-100,
                  ott_len=2, ott_pct=1.4,
                  tma_f=5, tma_m=20, tma_s=50):
    r, rb, rs = compute_rsi_signals(df["close"], n=rsi_n, ob=rsi_ob, os=rsi_os)
    c, cb, cs = compute_cci_signals(df, n=cci_n, upper=cci_up, lower=cci_lo)
    df2 = compute_ott(df.copy(), length=ott_len, percent=ott_pct, ma_type="EMA")
    ob, os = signals_price_vs_ott(df2)
    mf, mm, ms = compute_tma_series(df2["close"], fast=tma_f, mid=tma_m, slow=tma_s, ma_type="EMA")
    tb, ts = signals_tma_order(mf, mm, ms)
    sig_all = {"OTT": (ob, os), "TMA": (tb, ts), "CCI": (cb, cs), "RSI": (rb, rs)}
    return df2, sig_all

def rank_combos(df: pd.DataFrame, sig_all: dict, fee_bps: int):
    all_models = ["OTT", "CCI", "TMA", "RSI"]
    rows = []
    for ksize in range(1, len(all_models) + 1):
        for combo in combinations(all_models, ksize):
            pick = {x.lower(): sig_all[x] for x in combo}
            mode_specs = [("ANY", None), ("ALL", None)]
            max_vote = min(3, len(combo))
            for k_vote in range(2, max_vote + 1):
                mode_specs.append(("VOTE", k_vote))
            for mname, kval in mode_specs:
                e, x = combine(pick, mode=mname, k=kval, index=df.index)
                eq_c, net_c, pos_c, trades_c, _, _, _ = backtest_long_only(df, e, x, fee_bps=fee_bps, slip_bps=0)
                m_c = metrics(eq_c, net_c)
                label = mname if mname != "VOTE" else f"VOTE {kval}"
                rows.append({
                    "Combo": " & ".join(combo),
                    "Mode": label,
                    "Trades": int(trades_c),
                    "TotalReturn": m_c["TotalReturn"]
                })
    res = pd.DataFrame(rows).sort_values("TotalReturn", ascending=False).reset_index(drop=True)
    res["TotalReturn(%)"] = (res["TotalReturn"] * 100).round(2)
    return res[["Combo", "Mode", "Trades", "TotalReturn", "TotalReturn(%)"]]

if "search_results" not in st.session_state:
    st.session_state["search_results"] = []
if "selected_symbol" not in st.session_state:
    st.session_state["selected_symbol"] = None
if "pending_best" not in st.session_state:
    st.session_state["pending_best"] = False
if "models_sel" not in st.session_state:
    st.session_state["models_sel"] = ["OTT", "TMA", "CCI", "RSI"]
if "mode_sel" not in st.session_state:
    st.session_state["mode_sel"] = "NONE"
if "vote_k" not in st.session_state:
    st.session_state["vote_k"] = 2

df_all = load_data()
symbols = sorted(df_all["symbol"].unique().tolist())

row = st.columns([2.0, 0.9, 1.2, 1.0, 0.9])

with row[0]:
    st.markdown("<div class='header-label'>Symbol Search</div>", unsafe_allow_html=True)
    c1, c2 = st.columns([3, 1])
    query = c1.text_input("Symbol", value="", placeholder="e.g., XU100.IS, TUPRS.IS, NVDA, AAPL", label_visibility="collapsed")
    search_click = c2.button("Search", use_container_width=True)

with row[1]:
    st.markdown("<div class='header-label'>Initial Capital</div>", unsafe_allow_html=True)
    init_cap = float(st.number_input("Initial Capital", min_value=0.0, value=10000.0, step=100.0, label_visibility="collapsed"))

with row[2]:
    st.markdown("<div class='header-label'>Start Date</div>", unsafe_allow_html=True)
    max_cap_date = date(2025, 12, 31)
    start_dt = st.date_input("Start Date", value=date(2025, 1, 1), min_value=date(2015, 1, 1), max_value=max_cap_date, label_visibility="collapsed")

with row[3]:
    st.markdown("<div class='header-label'>Combine Mode</div>", unsafe_allow_html=True)
    mode_placeholder = st.empty()

with row[4]:
    st.markdown("<div class='header-label'>Fee (bps)</div>", unsafe_allow_html=True)
    fee_bps = int(st.number_input("Fee (bps)", min_value=0, max_value=100, value=20, step=1, label_visibility="collapsed"))

if search_click:
    q = query.strip()
    cand = []
    if q:
        cand.append(q.upper())
        if ".IS" not in q.upper():
            cand.append(q.upper() + ".IS")
    matches = [s for s in symbols if any(c in s for c in cand)]
    if len(matches) == 0:
        df_dates = pd.to_datetime(df_all["date"]) if not df_all.empty else pd.Series([], dtype="datetime64[ns]")
        start_min = str(df_dates.min().date()) if len(df_dates) else "2015-01-01"
        for c in cand:
            if fetch_and_append(c, start_min):
                df_all = load_data()
                symbols = sorted(df_all["symbol"].unique().tolist())
                matches = [c]
                break
        if len(matches) == 0:
            st.error("No data found for the given symbol.")
    st.session_state["search_results"] = matches
    st.session_state["selected_symbol"] = matches[0] if len(matches) == 1 else None
    st.session_state["pending_best"] = True
    st.rerun()

if len(st.session_state["search_results"]) == 0:
    st.info("Search a symbol to start.")
    st.stop()

if len(st.session_state["search_results"]) > 1 and st.session_state["selected_symbol"] is None:
    st.session_state["selected_symbol"] = st.selectbox("Select result", st.session_state["search_results"])

symbol = st.session_state["selected_symbol"] or st.session_state["search_results"][0]

df = df_all[df_all["symbol"] == symbol].copy().reset_index(drop=True)
df = df[df["date"] >= pd.to_datetime(start_dt)].reset_index(drop=True)

if not df.empty:
    last_row = df.iloc[-1]
    last_close = float(last_row["close"])
    last_dt = pd.to_datetime(last_row["date"]).date()
    exch, curr = symbol_meta(symbol)
    st.markdown(
        f"""
        <div style="
            margin: 0.5rem 0 1rem 0;
            padding: 0.6rem 0.9rem;
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 10px;
            display:flex; align-items:center; gap:0.8rem; flex-wrap:wrap;
        ">
            <span style="font-weight:600; font-size:1.05rem;">{symbol}</span>
            <span style="opacity:0.75;">Last close:</span>
            <span style="font-weight:700;">{last_close:,.2f}</span>
            <span style="opacity:0.6;">(as of {last_dt})</span>
            <span style="opacity:0.35;">•</span>
            <span style="opacity:0.75;">Exchange:</span>
            <span style="font-weight:600;">{exch}</span>
            <span style="opacity:0.35;">•</span>
            <span style="opacity:0.75;">Currency:</span>
            <span style="font-weight:600;">{curr}</span>
        </div>
        """,
        unsafe_allow_html=True
    )

df_sig_init, sig_all_init = build_signals(df)

if st.session_state["pending_best"]:
    rank_df_init = rank_combos(df_sig_init, sig_all_init, fee_bps=fee_bps)
    if not rank_df_init.empty:
        best = rank_df_init.sort_values("TotalReturn", ascending=False).iloc[0]
        st.session_state["models_sel"] = [s.strip() for s in str(best["Combo"]).split("&")]
        if best["Mode"].startswith("VOTE"):
            st.session_state["mode_sel"] = "VOTE"
            st.session_state["vote_k"] = int(best["Mode"].split()[1])
        else:
            st.session_state["mode_sel"] = str(best["Mode"])
        st.session_state["pending_best"] = False
        st.rerun()

with mode_placeholder:
    mode = st.selectbox(
        "Combine Mode",
        ["NONE", "ANY", "ALL", "VOTE"],
        index=["NONE","ANY","ALL","VOTE"].index(st.session_state["mode_sel"]),
        key="mode_sel",
        label_visibility="collapsed"
    )

side = st.sidebar.container()
models = side.multiselect("Models", ["OTT", "TMA", "CCI", "RSI"], default=st.session_state["models_sel"], key="models_sel")
rsi_n = int(side.number_input("RSI n", min_value=2, max_value=100, value=14, step=1))
rsi_ob = int(side.number_input("RSI overbought", min_value=50, max_value=100, value=70, step=1))
rsi_os = int(side.number_input("RSI oversold", min_value=0, max_value=50, value=30, step=1))
cci_n = int(side.number_input("CCI n", min_value=2, max_value=200, value=20, step=1))
cci_up = int(side.number_input("CCI upper", min_value=50, max_value=300, value=100, step=10))
cci_lo = int(side.number_input("CCI lower", min_value=-300, max_value=-50, value=-100, step=10))
ott_len = int(side.number_input("OTT length", min_value=1, max_value=50, value=2, step=1))
ott_pct = float(side.number_input("OTT percent", min_value=0.0, max_value=10.0, value=1.4, step=0.1))
tma_f = int(side.number_input("TMA fast", min_value=2, max_value=100, value=5, step=1))
tma_m = int(side.number_input("TMA mid", min_value=5, max_value=200, value=20, step=1))
tma_s = int(side.number_input("TMA slow", min_value=10, max_value=400, value=50, step=1))
vote_k = int(side.number_input("Vote k", min_value=1, max_value=4, value=st.session_state["vote_k"], step=1, key="vote_k"))

df_sig, sig_all = build_signals(df, rsi_n, rsi_ob, rsi_os, cci_n, cci_up, cci_lo, ott_len, ott_pct, tma_f, tma_m, tma_s)
mode = st.session_state["mode_sel"]

if mode != "NONE":
    sig_pick = {k.lower(): sig_all[k] for k in models}
    if len(sig_pick) == 0:
        st.warning("Select at least one model or choose NONE for buy & hold.")
        st.stop()
else:
    sig_pick = sig_all

entry, exit_ = combine(sig_pick if mode != "NONE" else sig_all, mode=mode, k=(st.session_state["vote_k"] if mode == "VOTE" else None), index=df_sig.index)

eq_raw, net, pos, trades, buys, sells, open_trades = backtest_long_only(df_sig, entry, exit_, fee_bps=fee_bps, slip_bps=0)
eq = eq_raw * init_cap
m = metrics(eq_raw, net)

buy_mask = (pos.shift(1).fillna(0) == 0) & (pos == 1)
sell_mask = (pos.shift(1).fillna(0) == 1) & (pos == 0)

buys_df = df_sig.loc[buy_mask, ["date", "close"]].rename(columns={"close": "price"})
sells_df = df_sig.loc[sell_mask, ["date", "close"]].rename(columns={"close": "price"})

intervals = []
buy_dates = df_sig.loc[buy_mask, "date"].tolist()
sell_dates = df_sig.loc[sell_mask, "date"].tolist()
si = 0
for bd in buy_dates:
    while si < len(sell_dates) and sell_dates[si] < bd:
        si += 1
    if si < len(sell_dates):
        intervals.append({"start": bd, "end": sell_dates[si]})
        si += 1
highlight_df = pd.DataFrame(intervals)

eq_buys_df = pd.DataFrame({"date": df_sig.loc[buy_mask, "date"], "equity": eq.loc[buy_mask].values})
eq_sells_df = pd.DataFrame({"date": df_sig.loc[sell_mask, "date"], "equity": eq.loc[sell_mask].values})

bh_ret = 0.0
if not df_sig.empty:
    first_close = float(df_sig["close"].iloc[0])
    last_close_bh = float(df_sig["close"].iloc[-1])
    if first_close > 0:
        bh_ret = (last_close_bh / first_close) - 1.0

strat_value = init_cap * (1.0 + float(m["TotalReturn"]))
bh_value = init_cap * (1.0 + float(bh_ret))

left, right = st.columns([2.3, 0.7])

with left:
    kpis = st.columns(6)  # 8 yerine 6 kolon

    kpis[0].metric("Strategy Return", f"{m['TotalReturn']*100:.2f}%")
    kpis[1].metric("Strategy Value", f"{strat_value:,.2f} {curr}")
    kpis[2].metric("Volatility", f"{m['Vol']*100:.2f}%")
    kpis[3].metric("Days", f"{m['Days']}")
    kpis[4].metric("Buys", f"{buys}")
    kpis[5].metric("Sells", f"{sells}")

    st.subheader(f"Price • {symbol}")
    price_base = alt.Chart(df_sig).mark_line().encode(
        x=alt.X("date:T", title=""),
        y=alt.Y("close:Q", title="Price")
    )
    price_buys = alt.Chart(buys_df).mark_point(size=60, filled=True, color="#00c853").encode(
        x="date:T", y="price:Q"
    )
    price_sells = alt.Chart(sells_df).mark_point(size=60, filled=True, color="#ff1744").encode(
        x="date:T", y="price:Q"
    )
    if not highlight_df.empty:
        price_highlight = alt.Chart(highlight_df).mark_rect(color="#00c853", opacity=0.5).encode(
            x="start:T", x2="end:T"
        )
        st.altair_chart(price_highlight + price_base + price_buys + price_sells, use_container_width=True)
    else:
        st.altair_chart(price_base + price_buys + price_sells, use_container_width=True)

    st.subheader(f"Equity • {symbol} • Mode: {mode} • Models: {', '.join(models) if mode != 'NONE' else 'Buy & Hold'}")
    eq_df = pd.DataFrame({"date": df_sig["date"], "equity": eq.values})
    eq_base = alt.Chart(eq_df).mark_line().encode(
        x=alt.X("date:T", title=""),
        y=alt.Y("equity:Q", title="Equity")
    )
    eq_buys = alt.Chart(eq_buys_df).mark_point(size=60, filled=True, color="#00c853").encode(
        x="date:T", y="equity:Q"
    )
    eq_sells = alt.Chart(eq_sells_df).mark_point(size=60, filled=True, color="#ff1744").encode(
        x="date:T", y="equity:Q"
    )
    if not highlight_df.empty:
        eq_highlight = alt.Chart(highlight_df).mark_rect(color="#00c853", opacity=0.5).encode(
            x="start:T", x2="end:T"
        )
        st.altair_chart(eq_highlight + eq_base + eq_buys + eq_sells, use_container_width=True)
    else:
        st.altair_chart(eq_base + eq_buys + eq_sells, use_container_width=True)

with right:
    st.markdown(
        f"""
        <div style="padding:12px 14px;border:1px solid rgba(255,255,255,.08);
                    border-radius:10px;margin-bottom:12px;background:rgba(255,255,255,.03)">
          <div style="font-weight:600;opacity:.85;margin-bottom:.4rem">
            Capital Snapshot
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:.5rem 1.25rem;align-items:end">
            <div>
              <div style="font-size:.8rem;opacity:.7">Buy &amp; Hold Return</div>
              <div style="font-size:1.1rem;font-weight:700">{bh_ret*100:.2f}%</div>
            </div>
            <div>
              <div style="font-size:.8rem;opacity:.7">Buy &amp; Hold Value</div>
              <div style="font-size:1.1rem;font-weight:700">{bh_value:,.2f} {curr}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.subheader("Model Performance")
    rank_df = rank_combos(df_sig, sig_all, fee_bps=fee_bps)
    rank_show = rank_df[["Combo", "Mode", "Trades", "TotalReturn(%)"]]
    st.dataframe(rank_show, use_container_width=True, height=520, hide_index=True)