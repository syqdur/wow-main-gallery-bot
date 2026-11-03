import aiohttp
import discord

WOW_EMOJI_SOURCES = {
    "wow_warrior": "https://wow.zamimg.com/images/wow/icons/large/classicon_warrior.jpg",
    "wow_paladin": "https://wow.zamimg.com/images/wow/icons/large/classicon_paladin.jpg",
    "wow_hunter": "https://wow.zamimg.com/images/wow/icons/large/classicon_hunter.jpg",
    "wow_rogue": "https://wow.zamimg.com/images/wow/icons/large/classicon_rogue.jpg",
    "wow_priest": "https://wow.zamimg.com/images/wow/icons/large/classicon_priest.jpg",
    "wow_deathknight": "https://wow.zamimg.com/images/wow/icons/large/classicon_deathknight.jpg",
    "wow_shaman": "https://wow.zamimg.com/images/wow/icons/large/classicon_shaman.jpg",
    "wow_mage": "https://wow.zamimg.com/images/wow/icons/large/classicon_mage.jpg",
    "wow_warlock": "https://wow.zamimg.com/images/wow/icons/large/classicon_warlock.jpg",
    "wow_monk": "https://wow.zamimg.com/images/wow/icons/large/classicon_monk.jpg",
    "wow_druid": "https://wow.zamimg.com/images/wow/icons/large/classicon_druid.jpg",
    "wow_demonhunter": "https://wow.zamimg.com/images/wow/icons/large/classicon_demonhunter.jpg",
    "wow_evoker": "https://wow.zamimg.com/images/wow/icons/large/classicon_evoker.jpg",
    "wow_tank": "https://wow.zamimg.com/images/wow/icons/large/ability_defend.jpg",
    "wow_healer": "https://wow.zamimg.com/images/wow/icons/large/spell_holy_flashheal.jpg",
    "wow_dps": "https://wow.zamimg.com/images/wow/icons/large/ability_dualwield.jpg"
}

CLASS_TO_EMOJI_NAME = {
    "Krieger": "wow_warrior",
    "Paladin": "wow_paladin",
    "Jäger": "wow_hunter",
    "Schurke": "wow_rogue",
    "Priester": "wow_priest",
    "Todesritter": "wow_deathknight",
    "Schamane": "wow_shaman",
    "Magier": "wow_mage",
    "Hexenmeister": "wow_warlock",
    "Mönch": "wow_monk",
    "Druide": "wow_druid",
    "Dämonenjäger": "wow_demonhunter",
    "Rufer": "wow_evoker"
}

async def install_wow_emojis(guild: discord.Guild) -> dict:
    """Lädt die echten WoW-Icons direkt auf den Discord-Server hoch, falls sie noch fehlen"""
    existing_emojis = {e.name: e for e in guild.emojis}
    created_count = 0

    headers = {"User-Agent": "Mozilla/5.0"}
    async with aiohttp.ClientSession(headers=headers) as session:
        for name, url in WOW_EMOJI_SOURCES.items():
            if name in existing_emojis:
                continue
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        img_data = await resp.read()
                        new_emoji = await guild.create_custom_emoji(name=name, image=img_data)
                        existing_emojis[name] = new_emoji
                        created_count += 1
            except Exception as e:
                print(f"Konnte Emoji {name} nicht erstellen: {e}")

    return {"existing": existing_emojis, "created": created_count}

def get_class_emoji_str(guild: discord.Guild, char_class: str) -> str:
    """Gibt das echte Custom-WoW-Emoji für die Klasse zurück"""
    emoji_name = CLASS_TO_EMOJI_NAME.get(char_class)
    if guild and emoji_name:
        for e in guild.emojis:
            if e.name == emoji_name:
                return str(e)
    # Fallback Unicode Emojis
    fallbacks = {
        "Krieger": "⚔️", "Paladin": "✨", "Jäger": "🏹", "Schurke": "🗡️",
        "Priester": "🕊️", "Todesritter": "💀", "Schamane": "⚡", "Magier": "🔮",
        "Hexenmeister": "🔥", "Mönch": "🥋", "Druide": "🌿", "Dämonenjäger": "👁️", "Rufer": "🐲"
    }
    return fallbacks.get(char_class, "⚔️")

def get_role_emoji_str(guild: discord.Guild, role_type: str) -> str:
    """Gibt das echte WoW-Rollen-Icon (Tank, Healer, DPS) zurück"""
    emoji_map = {
        "Tank": "wow_tank",
        "Heiler": "wow_healer",
        "DPS": "wow_dps"
    }
    target_name = emoji_map.get(role_type)
    if guild and target_name:
        for e in guild.emojis:
            if e.name == target_name:
                return f"{e} {role_type}"
    
    fallback_map = {
        "Tank": "🛡️ Tank",
        "Heiler": "💚 Heiler",
        "DPS": "⚔️ DPS"
    }
    return fallback_map.get(role_type, role_type)
