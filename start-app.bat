@echo off
title Cantek launcher

rem %~dp0 is the folder this script lives in, so the launcher works from any location
start "Cantek Backend" cmd /k "cd /d "%~dp0backend" && venv\Scripts\activate && uvicorn main:app --reload"
start "Cantek Website" cmd /k "cd /d "%~dp0frontend" && npm run dev"

timeout /t 8 /nobreak >nul
start "" http://cantek.localhost:5173/shop
