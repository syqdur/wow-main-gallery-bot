import os
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import database
from helpers import build_character_embed, WOW_CLASSES

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Modal für Charakter-Eingabe
class CharacterModal(discord.ui.Modal, title="WoW Main Charakter registrieren"):
    first_name = discord.ui.TextInput(
        label="Vorname (Charaktername)",
        placeholder="z.B. Arthas",
        max_length=32,
        required=True
    )
    last_name = discord.ui.TextInput(
        label="Nachname (optional)",
        placeholder="z.B. Menethil",
        max_length=32,
        required=False
    )
    char_class = discord.ui.TextInput(
        label="Klasse & Rasse",
        placeholder="z.B. Paladin (Mensch) oder Krieger (Untoter)",
        max_length=50,
        required=True
    )
    specs = discord.ui.TextInput(
        label="Main Spec & Dual Spec",
        placeholder="Format: Main-Spec | Dual-Spec (z.B. Vergeltung | Heilig)",
        max_length=100,
        required=True
    )
    image_and_armory = discord.ui.TextInput(
        label="Bild-URL & Armory (URL oder Link)",
        style=discord.TextStyle.paragraph,
        placeholder="Zeile 1: Bild-URL (z.B. https://i.imgur.com/...)\nZeile 2: Armory/Arsenal Link (optional)\nZeile 3+: Kurze Bio / Zitat (optional)",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        guild_id = interaction.guild_id

        first_name = self.first_name.value.strip()
        last_name = self.last_name.value.strip() if self.last_name.value else ""
        
        # Parse Class & Race
        class_input = self.char_class.value.strip()
        matched_class = "Krieger"
        race = ""
        for c in WOW_CLASSES:
            if c.lower() in class_input.lower():
                matched_class = c
                break
        if "(" in class_input and ")" in class_input:
            race = class_input[class_input.find("(")+1 : class_input.find(")")].strip()
        elif matched_class and matched_class.lower() != class_input.lower():
            race = class_input.replace(matched_class, "").strip(" ,-/")

        # Parse Specs
        specs_input = self.specs.value.strip()
        if "|" in specs_input:
            parts = specs_input.split("|", 1)
            main_spec = parts[0].strip()
            dual_spec = parts[1].strip()
        elif "/" in specs_input:
            parts = specs_input.split("/", 1)
            main_spec = parts[0].strip()
            dual_spec = parts[1].strip()
        else:
            main_spec = specs_input
            dual_spec = ""

        # Parse Image, Armory & Bio
        lines = [l.strip() for l in self.image_and_armory.value.split("\n") if l.strip()]
        image_url = None
        armory_url = None
        bio_lines = []

        for line in lines:
            if line.startswith("http://") or line.startswith("https://"):
                if any(ext in line.lower() for ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", "imgur", "discordapp"]):
                    if not image_url:
                        image_url = line
                        continue
                if not armory_url:
                    armory_url = line
                    continue
            bio_lines.append(line)

        bio = " ".join(bio_lines) if bio_lines else None

        # Speichern in DB
        await database.save_character(
            user_id=user_id,
            guild_id=guild_id,
            first_name=first_name,
            last_name=last_name,
            char_class=matched_class,
            main_spec=main_spec,
            dual_spec=dual_spec,
            race=race,
            image_url=image_url,
            armory_url=armory_url,
            bio=bio
        )

        char_data = {
            "first_name": first_name,
            "last_name": last_name,
            "char_class": matched_class,
            "main_spec": main_spec,
            "dual_spec": dual_spec,
            "race": race,
            "image_url": image_url,
            "armory_url": armory_url,
            "bio": bio
        }

        # Prüfen, ob Galerie-Kanal existiert
        gallery_channel_id = await database.get_gallery_channel(guild_id)
        gallery_status = "Dein Profil wurde gespeichert!"

        if gallery_channel_id:
            channel = interaction.guild.get_channel(gallery_channel_id)
            if channel:
                existing = await database.get_character(user_id, guild_id)
                embed = build_character_embed(interaction.user, char_data)
                
                # Wenn schon eine Nachricht existiert, editiere sie, sonst sende neu
                msg_id = existing["gallery_message_id"] if existing else None
                message_sent = False
                if msg_id:
                    try:
                        msg = await channel.fetch_message(msg_id)
                        await msg.edit(embed=embed)
                        message_sent = True
                        gallery_status += f" Dein Eintrag in {channel.mention} wurde aktualisiert!"
                    except Exception:
                        pass
                
                if not message_sent:
                    new_msg = await channel.send(embed=embed)
                    await database.update_gallery_message_id(user_id, guild_id, new_msg.id)
                    gallery_status += f" Dein Eintrag wurde in {channel.mention} gepostet!"

        embed_preview = build_character_embed(interaction.user, char_data)
        await interaction.followup.send(content=f"✅ **{gallery_status}**", embed=embed_preview, ephemeral=True)


@bot.event
async def on_ready():
    await database.init_db()
    try:
        synced = await bot.tree.sync()
        print(f"Eingeloggt als {bot.user} | {len(synced)} Slash-Commands synchronisiert.")
    except Exception as e:
        print(f"Fehler bei Command-Sync: {e}")


# Slash Command: Charakter eintragen
@bot.tree.command(name="charakter_eintragen", description="Trage deinen WoW Forever Main-Charakter für die Galerie ein")
async def charakter_eintragen(interaction: discord.Interaction):
    modal = CharacterModal()
    await interaction.response.send_modal(modal)


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
