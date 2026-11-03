import os
import io
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import database
from helpers import build_character_embed, CLASS_COLORS

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

WOW_CLASSES_CHOICES = [
    app_commands.Choice(name=name, value=name)
    for name in list(CLASS_COLORS.keys())
]

@bot.event
async def on_ready():
    await database.init_db()
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
        except Exception as e:
            print(f"Fehler bei Guild-Sync für {guild.name}: {e}")
    try:
        await bot.tree.sync()
        print(f"Eingeloggt als {bot.user} | Commands synchronisiert.")
    except Exception as e:
        print(f"Fehler bei Global-Sync: {e}")


# Slash Command: Charakter eintragen mit direktem Datei-Upload
@bot.tree.command(name="charakter_eintragen", description="Trage deinen WoW Main-Charakter mit Bild-Upload ein")
@app_commands.describe(
    vorname="Charaktername (Vorname)",
    klasse="Deine WoW Klasse",
    main_spec="Deine primäre Spezialisierung (z.B. Furor, Heilig, Schatten)",
    bild="Lade einen Screenshot oder ein Bild deines Charakters hoch (PNG/JPG/WEBP)",
    dual_spec="Deine Zweitspezialisierung (z.B. Schutz, Disziplin)",
    nachname="Nachname deines Charakters (optional)",
    rasse="Rasse deines Charakters (z.B. Nachtelf, Untoter, Zwerg)",
    armory="Link zu Armory/Arsenal (optional)",
    bio="Kurze Beschreibung, Rolle oder Zitat (optional)"
)
@app_commands.choices(klasse=WOW_CLASSES_CHOICES)
async def charakter_eintragen(
    interaction: discord.Interaction,
    vorname: str,
    klasse: app_commands.Choice[str],
    main_spec: str,
    bild: discord.Attachment = None,
    dual_spec: str = None,
    nachname: str = None,
    rasse: str = None,
    armory: str = None,
    bio: str = None
):
    await interaction.response.defer(ephemeral=True)

    user_id = interaction.user.id
    guild_id = interaction.guild_id

    # Vorheriges Profil prüfen (um Bild zu behalten falls keins neu hochgeladen wurde)
    existing = await database.get_character(user_id, guild_id)
    image_url = existing["image_url"] if existing else None
    old_msg_id = existing["gallery_message_id"] if existing else None

    # Falls eine neue Datei hochgeladen wurde:
    image_bytes = None
    attachment_filename = None
    if bild:
        # Prüfen, ob es sich um ein Bild handelt
        content_type = bild.content_type or ""
        if not content_type.startswith("image/"):
            await interaction.followup.send("⚠️ Die hochgeladene Datei ist kein gültiges Bild (bitte PNG, JPG oder WEBP hochladen).", ephemeral=True)
            return
        image_bytes = await bild.read()
        attachment_filename = bild.filename

    char_data = {
        "first_name": vorname.strip(),
        "last_name": nachname.strip() if nachname else "",
        "char_class": klasse.value,
        "main_spec": main_spec.strip(),
        "dual_spec": dual_spec.strip() if dual_spec else "",
        "race": rasse.strip() if rasse else "",
        "image_url": image_url,
        "armory_url": armory.strip() if armory else None,
        "bio": bio.strip() if bio else None
    }

    # Galerie-Kanal prüfen
    gallery_channel_id = await database.get_gallery_channel(guild_id)
    gallery_status = "Dein Charakterprofil wurde gespeichert!"

    if gallery_channel_id:
        channel = interaction.guild.get_channel(gallery_channel_id)
        if channel:
            # Alte Nachricht in der Galerie entfernen, um saubere Reihenfolge/Bilder zu gewährleisten
            if old_msg_id:
                try:
                    old_msg = await channel.fetch_message(old_msg_id)
                    await old_msg.delete()
                except Exception:
                    pass

            # Neue Nachricht im Galerie-Kanal posten
            if image_bytes and attachment_filename:
                file_for_channel = discord.File(io.BytesIO(image_bytes), filename=attachment_filename)
                embed_channel = build_character_embed(interaction.user, char_data, attachment_filename=attachment_filename)
                new_msg = await channel.send(embed=embed_channel, file=file_for_channel)
                if new_msg.attachments:
                    image_url = new_msg.attachments[0].url
                    char_data["image_url"] = image_url
            else:
                embed_channel = build_character_embed(interaction.user, char_data)
                new_msg = await channel.send(embed=embed_channel)

            await database.update_gallery_message_id(user_id, guild_id, new_msg.id)
            gallery_status += f" Dein Eintrag wurde in {channel.mention} ausgestellt!"
        else:
            gallery_status += " (Hinweis: Der Galerie-Kanal existiert nicht mehr. Bitte `/galerie_setup` erneut ausführen)."

    # Datenbank aktualisieren
    await database.save_character(
        user_id=user_id,
        guild_id=guild_id,
        first_name=char_data["first_name"],
        last_name=char_data["last_name"],
        char_class=char_data["char_class"],
        main_spec=char_data["main_spec"],
        dual_spec=char_data["dual_spec"],
        race=char_data["race"],
        image_url=image_url,
        armory_url=char_data["armory_url"],
        bio=char_data["bio"]
    )

    # Vorschau für den Nutzer
    if image_bytes and attachment_filename:
        file_preview = discord.File(io.BytesIO(image_bytes), filename=attachment_filename)
        embed_preview = build_character_embed(interaction.user, char_data, attachment_filename=attachment_filename)
        await interaction.followup.send(content=f"✅ **{gallery_status}**", embed=embed_preview, file=file_preview, ephemeral=True)
    else:
        embed_preview = build_character_embed(interaction.user, char_data)
        await interaction.followup.send(content=f"✅ **{gallery_status}**", embed=embed_preview, ephemeral=True)


# Slash Command: Profil ansehen
@bot.tree.command(name="profil", description="Zeige das Profil eines Spielers an")
@app_commands.describe(user="Der Spieler, dessen Charakter du sehen möchtest (Standard: du selbst)")
async def profil(interaction: discord.Interaction, user: discord.Member = None):
    target_user = user or interaction.user
    char = await database.get_character(target_user.id, interaction.guild_id)

    if not char:
        msg = f"{target_user.mention} hat bisher noch keinen Main-Charakter eingetragen."
        await interaction.response.send_message(msg, ephemeral=True)
        return

    embed = build_character_embed(target_user, dict(char))
    await interaction.response.send_message(embed=embed)


# Slash Command: Charakter löschen
@bot.tree.command(name="charakter_loeschen", description="Löscht deinen eingetragenen Main-Charakter")
async def charakter_loeschen(interaction: discord.Interaction):
    guild_id = interaction.guild_id
    user_id = interaction.user.id
    
    msg_id = await database.delete_character(user_id, guild_id)
    if msg_id:
        gallery_channel_id = await database.get_gallery_channel(guild_id)
        if gallery_channel_id:
            channel = interaction.guild.get_channel(gallery_channel_id)
            if channel:
                try:
                    msg = await channel.fetch_message(msg_id)
                    await msg.delete()
                except Exception:
                    pass

    await interaction.response.send_message("🗑️ Dein Charakterprofil und Galerie-Eintrag wurden gelöscht.", ephemeral=True)


# Admin Command: Galerie-Channel einrichten
@bot.tree.command(name="galerie_setup", description="Admin: Legt den Kanal für die Main-Galerie fest")
@app_commands.describe(channel="Der Kanal, in dem die Main-Charaktere ausgestellt werden")
@app_commands.default_permissions(administrator=True)
async def galerie_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    await database.set_gallery_channel(interaction.guild_id, channel.id)
    await interaction.response.send_message(f"✅ Main-Galerie Kanal wurde auf {channel.mention} gesetzt! Ab jetzt werden Charaktere dort automatisch gepostet und gepflegt.", ephemeral=True)


# Admin Command: Galerie neu synchronisieren
@bot.tree.command(name="galerie_sync", description="Admin: Baut die Galerie im konfigurierten Kanal komplett neu auf")
@app_commands.default_permissions(administrator=True)
async def galerie_sync(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    channel_id = await database.get_gallery_channel(interaction.guild_id)
    if not channel_id:
        await interaction.followup.send("⚠️ Es ist noch kein Galerie-Kanal definiert. Nutze zuerst `/galerie_setup`.")
        return

    channel = interaction.guild.get_channel(channel_id)
    if not channel:
        await interaction.followup.send("⚠️ Der konfigurierte Galerie-Kanal wurde nicht gefunden.")
        return

    chars = await database.list_guild_characters(interaction.guild_id)
    if not chars:
        await interaction.followup.send("Es sind bisher noch keine Charaktere eingetragen.")
        return

    count = 0
    for char in chars:
        user = interaction.guild.get_member(char["user_id"])
        if not user:
            try:
                user = await bot.fetch_user(char["user_id"])
            except Exception:
                user = None

        if user:
            embed = build_character_embed(user, dict(char))
            new_msg = await channel.send(embed=embed)
            await database.update_gallery_message_id(char["user_id"], interaction.guild_id, new_msg.id)
            count += 1

    await interaction.followup.send(f"✅ Galerie synchronisiert: {count} Charaktere in {channel.mention} gepostet.")


if __name__ == "__main__":
    if not TOKEN:
        print("FEHLER: Bitte erstelle eine .env-Datei mit DISCORD_TOKEN=dein_bot_token")
        exit(1)
    bot.run(TOKEN)
