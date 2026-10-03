# Stock Market Analysis Dashboard (pure Python)

Streamlit draws the dashboard, Plotly draws the charts, pandas does the maths.

## Files
- dashboard.py      - the dashboard (Steps 2, 7, 8, 9 + layout)
- data_provider.py  - Step 1: data source (Yahoo / Alpha Vantage / broker API)
- indicators.py     - Steps 3-7: % change, MA20/50, RSI, MACD, analysis text
- .env.example      - copied to .env by setup.bat (choose data provider / API keys)
- setup.bat / run.bat - one-click install and start (Windows)

## Run (easy way)
1. Double-click setup.bat (first time only, needs Python installed)
2. Double-click run.bat -> browser opens at http://127.0.0.1:8501

## Run (terminal way, from this folder)
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    pip install -r requirements.txt
    python -m streamlit run dashboard.py --server.headless true --server.address 127.0.0.1

## Symbols
US: AAPL, TSLA | India: RELIANCE, TCS (pick NSE/BSE) | Index: ^NSEI, ^BSESN, ^NSEBANK

## Viva notes
- Step 8 = st.fragment(run_every=N) re-runs the dashboard every N seconds.
- Step 9 = make_chart(): price+MA20/MA50, RSI, MACD in Plotly.
- Every indicator formula is hand-written in indicators.py.
- To use another API, edit only data_provider.py.
