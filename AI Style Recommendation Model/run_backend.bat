@echo off
echo ========================================
echo AI Fashion Recommendation System
echo ========================================
echo.
echo Starting backend server...
echo.

cd /d "%~dp0backend"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
