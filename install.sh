#!/usr/bin/env bash
set -e

echo "========================================================"
echo "  WoW Forever - Main Galerie Bot Installer (Linux / VPS)"
echo "========================================================"
echo ""

# 1. Systempakete aktualisieren und Python-Tools installieren
echo "[1/5] Installiere Systempakete (Python3, venv, pip)..."
if command -v apt-get &> /dev/null; then
    sudo apt-get update -qq
    sudo apt-get install -y -qq python3 python3-pip python3-venv
elif command -v dnf &> /dev/null; then
    sudo dnf install -y -q python3 python3-pip
fi

# 2. Virtuelle Umgebung erstellen
echo "[2/5] Erstelle venv..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# 3. Python-Pakete installieren
echo "[3/5] Installiere Python-Abhängigkeiten..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# 4. Token abfragen
echo "[4/5] Konfiguration (.env)..."
if [ ! -f ".env" ]; then
    read -rp "Bitte gib deinen Discord Bot Token ein: " BOT_TOKEN
    echo "DISCORD_TOKEN=$BOT_TOKEN" > .env
    echo ".env Datei erstellt."
else
    echo ".env Datei existiert bereits."
fi

# 5. Systemd Service für 24/7 Betrieb anlegen
echo ""
read -rp "Möchtest du einen systemd-Dienst einrichten, damit der Bot 24/7 im Hintergrund läuft? (j/n): " SETUP_SERVICE

if [[ "$SETUP_SERVICE" =~ ^[jJyY]$ ]]; then
    CURRENT_DIR=$(pwd)
    CURRENT_USER=$(whoami)
    SERVICE_FILE="/etc/systemd/system/wow-bot.service"

    echo "Erstelle systemd Service: $SERVICE_FILE..."
    sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=WoW Forever Main Galerie Discord Bot
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
WorkingDirectory=$CURRENT_DIR
ExecStart=$CURRENT_DIR/venv/bin/python $CURRENT_DIR/bot.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

    sudo systemctl daemon-reload
    sudo systemctl enable wow-bot
    sudo systemctl restart wow-bot
    echo ""
    echo "✅ Bot läuft jetzt als Hintergrunddienst!"
    echo "Status prüfen mit:  sudo systemctl status wow-bot"
    echo "Logs ansehen mit:    journalctl -u wow-bot -f"
    echo "Stoppen mit:         sudo systemctl stop wow-bot"
else
    echo ""
    echo "Installation abgeschlossen! Du kannst den Bot manuell starten mit:"
    echo "source venv/bin/activate && python bot.py"
fi

echo "========================================================"
