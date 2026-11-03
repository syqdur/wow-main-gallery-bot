import re
import aiohttp
from helpers import WOW_CLASSES

CLASS_TRANSLATIONS = {
    "warrior": "Krieger", "paladin": "Paladin", "hunter": "Jäger", "rogue": "Schurke",
    "priest": "Priester", "death knight": "Todesritter", "deathknight": "Todesritter",
    "shaman": "Schamane", "mage": "Magier", "warlock": "Hexenmeister",
    "monk": "Mönch", "druid": "Druide", "demon hunter": "Dämonenjäger", "evoker": "Rufer"
}

RACES = [
    "Mensch", "Human", "Zwerg", "Dwarf", "Nachtelf", "Night Elf", "Gnom", "Gnome",
    "Draenei", "Worgen", "Ork", "Orc", "Untoter", "Undead", "Taure", "Tauren",
    "Troll", "Blutelf", "Blood Elf", "Goblin", "Pandaren"
]

RACE_TRANSLATIONS = {
    "human": "Mensch", "dwarf": "Zwerg", "night elf": "Nachtelf", "gnome": "Gnom",
    "orc": "Ork", "undead": "Untoter", "tauren": "Taure", "troll": "Troll",
    "blood elf": "Blutelf"
}

async def fetch_armory_data(url: str) -> dict:
    """Ruft Armory-Webseite (Blizzard, ArmoryWoWForever, AOTC.gg etc.) ab und extrahiert Charakterdaten"""
    url = url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status != 200:
                raise ValueError(f"Armory-Seite nicht erreichbar (HTTP Status: {resp.status})")
            html = await resp.text()

    # 1. Meta-Tags extrahieren
    title_match = re.search(r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE) or \
                  re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
    
    desc_match = re.search(r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE) or \
                 re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
    
    image_match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE) or \
                  re.search(r'<meta\s+name=["\']twitter:image["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)

    raw_title = title_match.group(1).strip() if title_match else ""
    raw_desc = desc_match.group(1).strip() if desc_match else ""
    image_url = image_match.group(1).strip() if image_match else None

    # Name ermitteln
    # Häufig: "Name - Realm - World of Warcraft" oder "Vorname Nachname"
    clean_title = raw_title.split("-")[0].split("—")[0].split("|")[0].strip()
    name_parts = clean_title.split()
    first_name = name_parts[0] if name_parts else "Unbekannt"
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

    # Klasse ermitteln
    detected_class = "Krieger"
    search_text = (raw_title + " " + raw_desc + " " + html[:10000]).lower()
    for eng_class, de_class in CLASS_TRANSLATIONS.items():
        if re.search(r'\b' + re.escape(eng_class) + r'\b', search_text):
            detected_class = de_class
            break

    # Rasse ermitteln
    detected_race = ""
    for r in RACES:
        if re.search(r'\b' + re.escape(r.lower()) + r'\b', search_text):
            detected_race = RACE_TRANSLATIONS.get(r.lower(), r)
            break

    # Spec ermitteln
    specs_list = [
        "Vergeltung", "Heilig", "Schutz", "Furor", "Waffen", "Wiederherstellung",
        "Gleichgewicht", "Wildheit", "Wächter", "Schatten", "Disziplin", "Täuschung",
        "Meucheln", "Gesetzlosigkeit", "Treffsicherheit", "Tierherrschaft", "Überleben",
        "Frost", "Feuer", "Arkan", "Zerstörung", "Gebrechen", "Dämonologie",
        "Blut", "Unheilig", "Elementar", "Verstärkung", "Braumeister", "Nebelwirker", "Windläufer"
    ]
    detected_spec = "Main"
    for s in specs_list:
        if s.lower() in search_text:
            detected_spec = s
            break

    return {
        "first_name": first_name,
        "last_name": last_name,
        "char_class": detected_class,
        "race": detected_race,
        "main_spec": detected_spec,
        "dual_spec": "",
        "image_url": image_url,
        "armory_url": url,
        "bio": f"Importiert aus {url.split('/')[2]}"
    }
