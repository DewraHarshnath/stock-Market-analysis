@echo off
cd /d "%~dp0"
if not exist venv (
  echo Run setup.bat first.
  pause
  exit /b
)
call venv\Scripts\activate.bat
start "" cmd /c "timeout /t 6 >nul & start http://127.0.0.1:8501"
python -m streamlit run dashboard.py --server.headless true --server.address 127.0.0.1 --server.port 8501
pause
