"""Fetch stock history from the active data source."""

from __future__ import annotations

import pandas as pd


class YahooFinanceProvider:
    """Default provider used by the dashboard."""

    name = "yfinance"

    def get_history(self, symbol: str, period: str = "6mo", interval: str = "1d") -> pd.DataFrame:
        import yfinance as yf

        df = yf.download(
            symbol,
            period=period,
            interval=interval,
            progress=False,
            auto_adjust=True,
            threads=False,
        )
        if df.empty:
            raise ValueError(
                f"No data returned for symbol '{symbol}'. "
                "Check the ticker is correct (e.g. 'AAPL', 'INFY.NS')."
            )

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df.reset_index()
        date_col = "Date" if "Date" in df.columns else "Datetime"
        return df[[date_col, "Close"]].rename(columns={date_col: "Date"})


def get_provider():
    """Return the only active provider used by the dashboard."""
    return YahooFinanceProvider()
