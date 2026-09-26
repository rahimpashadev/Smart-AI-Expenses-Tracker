@echo off
echo Starting Backend Server...
cd /d "%~dp0"
py -m uvicorn app:app --reload
pause
