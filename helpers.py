import discord

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

# WoW Klassenliste
WOW_CLASSES = list(CLASS_COLORS.keys())

def get_class_color(char_class: str) -> int:
    return CLASS_COLORS.get(char_class, 0x5865F2)

def build_character_embed(user: discord.User | discord.Member, char_data) -> discord.Embed:
    first_name = char_data["first_name"]
    last_name = char_data["last_name"]
    full_name = f"{first_name} {last_name}".strip() if last_name else first_name
    char_class = char_data["char_class"]
    main_spec = char_data["main_spec"]
    dual_spec = char_data["dual_spec"]
    race = char_data.get("race")
    image_url = char_data.get("image_url")
    armory_url = char_data.get("armory_url")
    bio = char_data.get("bio")

    color = get_class_color(char_class)
    embed = discord.Embed(
        title=f"⚔️ {full_name}",
        description=bio if bio else None,
        color=color
    )

    embed.set_author(name=f"Spieler: {user.display_name}", icon_url=user.display_avatar.url if user.display_avatar else None)
    
    # Details Fields
    class_race = f"{race} {char_class}".strip() if race else char_class
    embed.add_field(name="🛡️ Klasse & Rasse", value=class_race, inline=True)
    embed.add_field(name="🗡️ Main Spec", value=main_spec, inline=True)
    
    if dual_spec:
        embed.add_field(name="🔄 Dual Spec", value=dual_spec, inline=True)
    else:
        embed.add_field(name="🔄 Dual Spec", value="*Keiner*", inline=True)

    if armory_url:
        embed.add_field(name="🔗 Armory / Link", value=f"[Arsenal Profil]({armory_url})", inline=False)

    if image_url:
        embed.set_image(url=image_url)

    embed.set_footer(text="WoW Forever • Main Galerie")
    return embed
