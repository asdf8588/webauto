@echo off
chcp 65001 >nul
title WebAuto Test Platform

echo ================================================
echo    WebAuto Test Platform
echo ================================================
echo.

cd /d "%~dp0platform\backend"

REM Create venv if not exists
if not exist ".venv" (
    echo [1/3] Creating virtual environment...
    python -m venv .venv
    echo [1/3] Done
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies
echo [2/3] Installing dependencies...
pip install -q django djangorestframework django-cors-headers pyyaml requests 2>nul

REM Run migrations
echo [3/3] Running migrations...
python manage.py migrate --run-syncdb 2>nul

REM Start server
echo.
echo ================================================
echo    Starting Server...
echo ================================================
echo.
echo    Open: http://localhost:8000
echo.
python manage.py runserver 8000
