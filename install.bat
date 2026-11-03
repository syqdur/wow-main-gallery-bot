@echo off
chcp 65001 >nul
title WoW Forever Bot Installer (Windows)

echo ========================================================
echo   WoW Forever - Main Galerie Bot Installer (Windows)
echo ========================================================
echo.

:: 1. Prüfen, ob Python installiert ist
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FEHLER] Python wurde nicht gefunden!
    echo Bitte installiere Python 3.10+ von https://www.python.org/downloads/
    echo Achte darauf, das Häkchen bei "Add Python to PATH" zu setzen.
    echo.
    pause
    exit /b 1
)

echo [1/4] Python gefunden.
echo.

:: 2. Virtuelle Umgebung (venv) anlegen
if not exist "venv" (
    echo [2/4] Erstelle virtuelle Umgebung (.venv)...
    python -m venv venv
) else (
    echo [2/4] Virtuelle Umgebung existiert bereits.
)

:: 3. Abhängigkeiten installieren
echo [3/4] Installiere Abhängigkeiten aus requirements.txt...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [FEHLER] Beim Installieren der Bibliotheken gab es ein Problem.
    pause
    exit /b 1
)

:: 4. .env Datei einrichten
if not exist ".env" (
    echo.
    echo [4/4] Konfiguration:
    set /p BOT_TOKEN="Bitte gib deinen Discord Bot Token ein: "
    echo DISCORD_TOKEN=%BOT_TOKEN%> .env
    echo .env Datei wurde erfolgreich erstellt!
) else (
    echo [4/4] .env Konfigurationsdatei existiert bereits.
)

echo.
echo ========================================================
echo   Installation erfolgreich abgeschlossen!
echo ========================================================
echo Du kannst den Bot nun jederzeit mit start.bat starten.
echo.
pause
