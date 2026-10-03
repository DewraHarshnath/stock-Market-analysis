@echo off
cd /d "%~dp0"
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
copy /y .env.example .env >nul
echo.
echo Setup finished. Now double-click run.bat
pause
