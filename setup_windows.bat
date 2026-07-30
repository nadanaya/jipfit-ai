@echo off
setlocal
cd /d %~dp0
python -m venv .venv
call .venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python scripts\bootstrap.py
python scripts\validate_project.py

echo.
echo Setup complete. Start the app with run_app.bat
pause
