@echo off
title AutoClip Pro - Backend Engine
echo ====================================================
echo  Starting AutoClip Pro Backend (FastAPI + AI Engine)
echo ====================================================
call backend\venv\Scripts\activate.bat
python backend\run_server.py
pause
