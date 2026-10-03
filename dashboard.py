"""
dashboard.py
------------
Pure-Python frontend (Streamlit + Plotly). No HTML/CSS/JS needed.

Pipeline (same 9 steps as before):
  1 fetch data          -> data_provider.py
  2 raw data table      -> st.dataframe
  3 % change            -> indicators.pct_change
  4 MA20 / MA50         -> indicators.moving_average
  5 RSI                 -> indicators.rsi
  6 MACD                -> indicators.macd
  7 analysis text       -> indicators.generate_analysis_text
  8 continuous update   -> st.fragment(run_every=...)
  9 graph               -> plotly

Run with:
    streamlit run dashboard.py
"""
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv
from plotly.subplots import make_subplots

from data_provider import get_provider
from indicators import (generate_analysis_text, macd, moving_average,
                        pct_change, rsi)

load_dotenv()
st.set_page_config(page_title="Stock Market Analysis", layout="wide")

INDIAN_INDICES = {"^NSEI", "^BSESN", "^NSEBANK"}
MARKETS = {
    "US (e.g. AAPL)": "",
    "India NSE (e.g. RELIANCE)": ".NS",
    "India BSE (e.g. RELIANCE)": ".BO",
    "Index (type ^symbol)": "",
}


def build_symbol(base: str, suffix: str) -> str:
    """Add .NS / .BO for Indian stocks. Index symbols (^NSEI) are left alone."""
    base = base.strip().upper() or "AAPL"
    if base.startswith("^") or not suffix or base.endswith(suffix):
        return base
    return base + suffix


def currency_for(symbol: str) -> str:
    if symbol.endswith((".NS", ".BO")) or symbol in INDIAN_INDICES:
        return "₹"
    return "$"


@st.cache_data(ttl=4, show_spinner=False)
def load_data(symbol: str, period: str, interval: str) -> pd.DataFrame:
    """Steps 1-6: fetch data and add every indicator column."""
    df = get_provider().get_history(symbol, period=period, interval=interval)
    closes = df["Close"]
    df["pct_change"] = pct_change(closes)
    df["ma20"] = moving_average(closes, 20)
    df["ma50"] = moving_average(closes, 50)
    df["rsi"] = rsi(closes, 14)
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(closes)
    return df


def num(v, default=float("nan")) -> float:
    return float(v) if pd.notna(v) else default


def make_chart(df: pd.DataFrame, cur: str) -> go.Figure:
    """Step 9: price + MAs on top, RSI in the middle, MACD at the bottom."""
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        row_heights=[0.55, 0.2, 0.25], vertical_spacing=0.04,
                        subplot_titles=("Price with MA20 / MA50", "RSI (14)", "MACD"))
    x = df["Date"]
    fig.add_trace(go.Scatter(x=x, y=df["Close"], name="Close", line=dict(color="#dbe2ea")), 1, 1)
    fig.add_trace(go.Scatter(x=x, y=df["ma20"], name="MA20", line=dict(color="#e7b64f")), 1, 1)
    fig.add_trace(go.Scatter(x=x, y=df["ma50"], name="MA50", line=dict(color="#3ecf8e")), 1, 1)

    fig.add_trace(go.Scatter(x=x, y=df["rsi"], name="RSI", line=dict(color="#8ab4f8")), 2, 1)
    fig.add_hline(y=70, line_dash="dot", line_color="#e8637a", row=2, col=1)
    fig.add_hline(y=30, line_dash="dot", line_color="#3ecf8e", row=2, col=1)

    colors = ["#3ecf8e" if v >= 0 else "#e8637a" for v in df["macd_hist"].fillna(0)]
    fig.add_trace(go.Bar(x=x, y=df["macd_hist"], name="Histogram", marker_color=colors), 3, 1)
    fig.add_trace(go.Scatter(x=x, y=df["macd"], name="MACD", line=dict(color="#dbe2ea")), 3, 1)
    fig.add_trace(go.Scatter(x=x, y=df["macd_signal"], name="Signal", line=dict(color="#e7b64f")), 3, 1)

    fig.update_layout(template="plotly_dark", height=720, margin=dict(l=10, r=10, t=40, b=10),
                      legend=dict(orientation="h", y=1.06), hovermode="x unified")
    fig.update_yaxes(title_text=cur, row=1, col=1)
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    return fig


# ---------------- Sidebar controls ----------------
st.title("Stock Market Analysis")

with st.sidebar:
    st.header("Settings")
    market = st.selectbox("Market", list(MARKETS.keys()))
    base = st.text_input("Symbol", value="AAPL",
                         help="US: AAPL, TSLA · India: RELIANCE, TCS · Index: ^NSEI, ^BSESN, ^NSEBANK")
    view = st.radio("View", ["Today (intraday)", "Historical"])
    if view == "Today (intraday)":
        period = "1d"  # latest trading session (works on weekends/holidays too)
        interval = st.selectbox("Candle size", ["1m", "5m", "15m"], index=1)
    else:
        period = st.selectbox("History", ["5d", "1mo", "3mo", "6mo", "1y", "2y"], index=3)
        interval = st.selectbox("Interval", ["1d", "1h", "15m", "5m"], index=0)
    auto = st.checkbox("Auto-refresh (Step 8)", value=True)
    every = st.slider("Refresh every (seconds)", 5, 60, 10)
    st.caption("Indices: Nifty 50 = ^NSEI · Sensex = ^BSESN · Bank Nifty = ^NSEBANK")

symbol = build_symbol(base, MARKETS[market])


# ---------------- Main dashboard (re-runs itself every N seconds) ----------------
@st.fragment(run_every=every if auto else None)
def dashboard():
    try:
        df = load_data(symbol, period, interval)
    except Exception as e:
        st.error(f"Error: {e}")
        return

    cur = currency_for(symbol)
    last = df.iloc[-1]
    price, pct = num(last["Close"]), num(last["pct_change"], 0.0)

    st.subheader(f"{symbol}")
    c1, c2, c3, c4, c5 = st.columns(5)
    intraday = view == "Today (intraday)"
    if intraday:
        day_pct = (price / num(df["Close"].iloc[0]) - 1) * 100
        c1.metric("Price", f"{cur}{price:,.2f}", f"{day_pct:+.2f}% today")
    else:
        c1.metric("Price", f"{cur}{price:,.2f}", f"{pct:+.2f}%")
    c2.metric("MA20", f"{cur}{num(last['ma20']):,.2f}")
    c3.metric("MA50", f"{cur}{num(last['ma50']):,.2f}")
    c4.metric("RSI (14)", f"{num(last['rsi']):.1f}")
    c5.metric("MACD / Signal", f"{num(last['macd']):.3f}", f"signal {num(last['macd_signal']):.3f}",
              delta_color="off")

    st.info(generate_analysis_text(
        symbol=symbol, last_price=price, last_pct=pct,
        ma20=num(last["ma20"]), ma50=num(last["ma50"]), last_rsi=num(last["rsi"], 50.0),
        last_macd=num(last["macd"]), last_signal=num(last["macd_signal"])))

    st.plotly_chart(make_chart(df if intraday else df.tail(120), cur), width="stretch")
    if len(df) < 50:
        st.caption(f"Only {len(df)} candles loaded - MA50 needs 50. Use a smaller candle size.")

    st.markdown("**Recent data (raw)**")
    raw = df[["Date", "Close", "pct_change"]].tail(10).iloc[::-1].copy()
    raw["Date"] = pd.to_datetime(raw["Date"]).dt.strftime("%d %b %Y" if interval == "1d" else "%d %b %H:%M")
    raw["Close"] = raw["Close"].map(lambda v: f"{cur}{v:,.2f}")
    raw["pct_change"] = raw["pct_change"].map(lambda v: f"{v:+.2f}%" if pd.notna(v) else "—")
    st.dataframe(raw.rename(columns={"pct_change": "% Change"}), hide_index=True, width="stretch")

    st.caption(f"source: {get_provider().name} · last update: {datetime.now():%H:%M:%S}")


dashboard()
