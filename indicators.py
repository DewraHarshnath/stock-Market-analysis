"""
indicators.py
-------------
All the technical-analysis maths lives here, kept deliberately simple
and commented so it's easy to explain in a viva/project demo.

Every function takes a pandas Series of closing prices and returns
either a pandas Series (same length, aligned by index) or a single
float for the "latest" value.
"""

import pandas as pd
import numpy as np


def pct_change(closes: pd.Series) -> pd.Series:
    """Step 3: percentage change between each price and the previous one."""
    return closes.pct_change() * 100


def moving_average(closes: pd.Series, window: int) -> pd.Series:
    """Step 4: simple moving average (SMA) over `window` periods."""
    return closes.rolling(window=window).mean()


def rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    """
    Step 5: Relative Strength Index.
    RSI = 100 - (100 / (1 + RS)), where RS = avg gain / avg loss
    over the last `period` price changes.
    """
    delta = closes.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    return rsi_series.fillna(50)  # neutral default while warming up


def macd(closes: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """
    Step 6: MACD (Moving Average Convergence Divergence).
    Returns three aligned Series: macd_line, signal_line, histogram.
    """
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def generate_analysis_text(symbol: str, last_price: float, last_pct: float,
                            ma20: float, ma50: float, last_rsi: float,
                            last_macd: float, last_signal: float) -> str:
    """Step 7: turn the numbers into a plain-English summary."""
    trend = "no clear trend yet (not enough data)"
    if not np.isnan(ma20) and not np.isnan(ma50):
        trend = "an uptrend" if ma20 > ma50 else "a downtrend"

    rsi_note = "RSI is in a neutral range."
    if last_rsi > 70:
        rsi_note = "RSI is above 70, suggesting the stock may be overbought."
    elif last_rsi < 30:
        rsi_note = "RSI is below 30, suggesting the stock may be oversold."

    macd_note = "MACD data is still warming up."
    if not np.isnan(last_macd) and not np.isnan(last_signal):
        macd_note = (
            "MACD is above its signal line, a bullish momentum signal."
            if last_macd > last_signal else
            "MACD is below its signal line, a bearish momentum signal."
        )

    direction = "up" if last_pct >= 0 else "down"
    return (
        f"{symbol} is trading at {last_price:.2f}, {direction} {abs(last_pct):.2f}% "
        f"on the last update, and is in {trend} based on its 20/50-period "
        f"moving averages. {rsi_note} {macd_note}"
    )
