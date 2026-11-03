import discord
from datetime import datetime

# Offizielle World of Warcraft Klassenfarben (Hex)
CLASS_COLORS = {
    "Krieger": 0xC79C6E,
    "Paladin": 0xF58CBA,
    "Jäger": 0xABD473,
    "Schurke": 0xFFF569,
    "Priester": 0xFFFFFF,
    "Todesritter": 0xC41E3A,
    "Schamane": 0x0070DE,
    "Magier": 0x40C7EB,
    "Hexenmeister": 0x8787ED,
    "Mönch": 0x00FF96,
    "Druide": 0xFF7D0A,
    "Dämonenjäger": 0xA330C9,
    "Rufer": 0x33937F
}

# Wowhead CDN Icons für Klassen-Wappen
CLASS_ICONS = {
    "Krieger": "https://wow.zamimg.com/images/wow/icons/large/classicon_warrior.jpg",
    "Paladin": "https://wow.zamimg.com/images/wow/icons/large/classicon_paladin.jpg",
    "Jäger": "https://wow.zamimg.com/images/wow/icons/large/classicon_hunter.jpg",
    "Schurke": "https://wow.zamimg.com/images/wow/icons/large/classicon_rogue.jpg",
    "Priester": "https://wow.zamimg.com/images/wow/icons/large/classicon_priest.jpg",
    "Todesritter": "https://wow.zamimg.com/images/wow/icons/large/classicon_deathknight.jpg",
    "Schamane": "https://wow.zamimg.com/images/wow/icons/large/classicon_shaman.jpg",
    "Magier": "https://wow.zamimg.com/images/wow/icons/large/classicon_mage.jpg",
    "Hexenmeister": "https://wow.zamimg.com/images/wow/icons/large/classicon_warlock.jpg",
    "Mönch": "https://wow.zamimg.com/images/wow/icons/large/classicon_monk.jpg",
    "Druide": "https://wow.zamimg.com/images/wow/icons/large/classicon_druid.jpg",
    "Dämonenjäger": "https://wow.zamimg.com/images/wow/icons/large/classicon_demonhunter.jpg",
    "Rufer": "https://wow.zamimg.com/images/wow/icons/large/classicon_evoker.jpg"
}

# WoW Emojis für Klassen
CLASS_EMOJIS = {
    "Krieger": "⚔️",
    "Paladin": "✨",
    "Jäger": "🏹",
    "Schurke": "🗡️",
    "Priester": "🕊️",
    "Todesritter": "💀",
    "Schamane": "⚡",
    "Magier": "🔮",
    "Hexenmeister": "🔥",
    "Mönch": "🥋",
    "Druide": "🌿",
    "Dämonenjäger": "👁️",
    "Rufer": "🐲"
}

WOW_CLASSES = list(CLASS_COLORS.keys())

def get_role_badge(spec: str) -> str:
    """Ermittelt Rollen-Icon anhand der Spezialisierung"""
    if not spec:
        return ""
    s = spec.lower()
    # Tanks
    if any(t in s for t in ["schutz", "prot", "blut", "blood", "braumeister", "brewmaster", "wächter", "guardian"]):
        return "🛡️ Tank"
    # Heiler
    if any(h in s for t in ["heilig", "holy", "disziplin", "discipline", "wiederherstellung", "resto", "nebelwirker", "mistweaver", "bewahrung", "preservation"] for h in [t]):
        return "💚 Heiler"
    # DPS
    return "⚔️ DPS"

def build_character_embed(user: discord.User | discord.Member, char_data, attachment_filename: str = None) -> discord.Embed:
    first_name = char_data.get("first_name", "")
    last_name = char_data.get("last_name") or ""
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    char_class = char_data.get("char_class", "Krieger")
    main_spec = char_data.get("main_spec", "-")
    dual_spec = char_data.get("dual_spec") or ""
    race = char_data.get("race") or ""
    image_url = char_data.get("image_url")
    armory_url = char_data.get("armory_url")
    bio = char_data.get("bio")

    color = CLASS_COLORS.get(char_class, 0xC79C6E)
    class_emoji = CLASS_EMOJIS.get(char_class, "⚔️")
    class_icon_url = CLASS_ICONS.get(char_class)

    # Rollen-Tags
    main_role = get_role_badge(main_spec)
    dual_role = get_role_badge(dual_spec) if dual_spec else None

    # Stylischer Titel mit WoW Header
    embed = discord.Embed(
        title=f"👑  {full_name}",
        color=color
    )

    # Stylische Beschreibung / Zitat
    desc_lines = []
    if bio:
        desc_lines.append(f"> *„{bio}“*\n")
    desc_lines.append("───────────────────────────────")
    embed.description = "\n".join(desc_lines)

    # Author Header mit Discord Spieler
    if user:
        embed.set_author(
            name=f"Kader • {user.display_name}",
            icon_url=user.display_avatar.url if user.display_avatar else None
        )

    # Klasse & Rasse Field
    race_str = f"{race} " if race else ""
    embed.add_field(
        name="⚜️  Klasse & Volk",
        value=f"**{class_emoji} {race_str}{char_class}**",
        inline=True
    )

    # Main-Spec Field
    embed.add_field(
        name="🗡️  Main-Skillung",
        value=f"**{main_spec}**\n`{main_role}`",
        inline=True
    )

    # Dual-Spec Field
    if dual_spec:
        embed.add_field(
            name="🔄  Dual-Skillung",
            value=f"**{dual_spec}**\n`{dual_role}`",
            inline=True
        )
    else:
        embed.add_field(
            name="🔄  Dual-Skillung",
            value="*Keine*",
            inline=True
        )

    # Armory-Link
    if armory_url:
        embed.add_field(
            name="📜  Arsenal",
            value=f"[WoW Forever Profil ansehen ↗]({armory_url})",
            inline=False
        )

    # Thumbnail: Offizielles WoW-Klassen-Wappen
    if class_icon_url:
        embed.set_thumbnail(url=class_icon_url)

    # Großes Charakter-Bild / Screenshot
    if attachment_filename:
        embed.set_image(url=f"attachment://{attachment_filename}")
    elif image_url:
        embed.set_image(url=image_url)

    # Footer mit Zeitstempel & Branding
    now_str = datetime.now().strftime("%d.%m.%Y")
    embed.set_footer(
        text=f"WoW Forever • Main Galerie • {now_str}",
        icon_url="https://wow.zamimg.com/images/wow/icons/large/inv_misc_book_09.jpg"
    )

    return embed
