# WoW Forever – Main Galerie Discord Bot ⚔️

Ein moderner Discord-Bot für World of Warcraft Communities und Gilden (z.B. WoW Forever), mit dem Mitglieder ihren **Main-Charakter** eintragen und in einer automatischen **Main-Galerie** präsentieren können.

---

## 📖 Was ist eine "Main Galerie"?

In WoW-Gilden und Realm-Discords ist eine **Main-Galerie** ein gesperrter/moderierter Kanal (z.B. `#main-galerie` oder `#kader`), in dem der Bot für jedes registrierte Mitglied eine ansprechende **Charakter-Karte (Embed)** ausstellt:
- **Übersicht für Raids & Gilde:** Wer spielt welche Klasse und Spezialisierung (inkl. Dual-Spec)?
- **Optischer Showcase:** Screenshots des Charakters (Transmog/Ausrüstung) im Großformat.
- **Sauber & Duplikatfrei:** Ändert ein Spieler seine Skillung, Ausrüstung oder das Bild, aktualisiert der Bot automatisch die bestehende Karte im Kanal, anstatt den Chat zuzuspammen.
- **Vorbereitet für Armory-Import:** Unterstützt Profil-Links (Blizzard Arsenal, Raider.io oder private Realm-APIs).

---

## ✨ Features

- 📝 **Interaktives Eingabe-Formular (Discord Modal):**
  - **Vor- & Nachname:** z.B. *Valas Duskstrider* oder *Arthas Menethil*
  - **Klasse & Rasse:** Farbkodiert in den **offiziellen WoW-Klassenfarben** (z.B. Druiden-Orange, Magier-Hellblau, Paladin-Pink).
  - **Main-Spec & Dual-Spec:** z.B. *Furor (Main) | Schutz (Dual)*
  - **Charakterbild / Screenshot:** URL zu einem Screenshot oder Render.
  - **Armory-Link & Kurzbeschreibung:** Für spätere Arsenal-Imports oder RP-Hintergrund.
- 🖼️ **Automatische Galerie-Verwaltung:**
  - `/galerie_setup #kanal` legt den Schaukasten fest.
  - Änderungen überschreiben automatisch die alte Karte.
- 🔍 **Befehle:**
  - `/charakter_eintragen` – Öffnet das Popup-Formular.
  - `/profil [user]` – Zeigt die Charakterkarte eines bestimmten Spielers an.
  - `/charakter_loeschen` – Entfernt das Profil und löscht die Karte aus der Galerie.
  - `/galerie_setup #kanal` – Legt den Kanal für die Main-Galerie fest (Admin).
  - `/wow_icons_installieren` – Installiert originale WoW-Emojis auf dem Server (Admin).

---

## 🔒 Stream-Talk PIN-Sicherheitssystem

Schützt die Live-Stream-Talks (`Syq LIVE` und `DerOnkel LIVE`) durch 4-stellige PINs:
- **`Syq LIVE`**: PIN **`2407`**
- **`DerOnkel LIVE`**: PIN **`9536`**

### Wie es funktioniert:
1. **Für Mitglieder:**
   - Klick auf den Button **🔑 Stream-Talk beitreten (PIN)** im Kanal `#streaming-infos` oder Eingabe von `/stream_pin pin:2407`.
   - Bei korrektem PIN wird der Kanal für das Mitglied freigeschaltet (und wenn der User bereits in einem Sprachkanal sitzt, wird er sofort hineinverschoben).
2. **Strikte Einweg-Sperre:**
   - Sobald das Mitglied den Sprachkanal verlässt, entzieht der Bot die Berechtigung **sofort automatisch**.
   - Jedes Mitglied muss bei jedem neuen Beitritt erneut den PIN eingeben!
3. **Admin-Setup:**
   - `/stream_pin_setup channel:#streaming-infos` postet die dauerhafte interaktive Beitritts-Box mit Button in den gewünschten Kanal.

---

## 🚀 Schnelle 1-Klick Installation

Im Projektordner liegen fertige Installations-Skripte für Windows und Linux/VPS bereit:

### A. Windows (Lokal)
1. Stelle sicher, dass [Python](https://www.python.org/downloads/) installiert ist (beim Setup *"Add Python to PATH"* anhaken).
2. Doppelklicke auf [`install.bat`](file:///C:/Users/Mauro/.gemini/antigravity/scratch/wow-main-gallery-bot/install.bat) – das Skript richtet automatisch die Umgebung ein, fragt deinen Bot-Token ab und speichert ihn in `.env`.
3. Starte den Bot mit [`start.bat`](file:///C:/Users/Mauro/.gemini/antigravity/scratch/wow-main-gallery-bot/start.bat).

### B. Linux VPS (z.B. Ubuntu / Debian für 24/7 Betrieb)
1. Übertrage den Ordner auf deinen VPS (oder klone ihn).
2. Führe im Ordner folgendes aus:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
3. Das Skript fragt deinen Token ab und kann automatisch einen **systemd-Dienst** anlegen, sodass der Bot 24/7 im Hintergrund läuft und bei Server-Neustarts automatisch wieder startet.

---

## 🔮 Zukünftiger Armory-Import

Der Bot speichert bereits ein Feld `armory_url`. Sobald die WoW Forever Realm-API oder ein offizielles Arsenal bereitsteht, kann ein Scraper/API-Client im Bot eingebaut werden, der Gearscore, Itemlevel und Ausrüstung automatisch abruft.
