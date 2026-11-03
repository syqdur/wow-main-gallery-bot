@echo off
chcp 65001 >nul
title WoW Forever Bot

if not exist "venv\Scripts\activate.bat" (
    echo [FEHLER] Bitte führe zuerst install.bat aus!
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
echo Starte WoW Forever Main Galerie Bot...
python bot.py
pause
