import os
import io
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import database
from helpers import build_character_embed, WOW_CLASSES

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

# Reine Standard-Intents (keine Privileged Intents nötig, läuft 100% stabil)
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Modal (Popup-Fenster)
class CharacterModal(discord.ui.Modal, title="WoW Charakter eintragen"):
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
        placeholder="z.B. Paladin (Mensch) oder Krieger",
        max_length=50,
        required=True
    )
    specs = discord.ui.TextInput(
        label="Main-Spec & Dual-Spec",
        placeholder="z.B. Vergeltung | Heilig",
        max_length=80,
        required=True
    )
    extra_info = discord.ui.TextInput(
        label="Bio / Armory (optional)",
        style=discord.TextStyle.paragraph,
        placeholder="Kurze Beschreibung oder Arsenal-Link",
        max_length=300,
        required=False
    )

    def __init__(self, uploaded_file: discord.Attachment = None):
        super().__init__()
        self.uploaded_file = uploaded_file

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        user_id = interaction.user.id
        guild_id = interaction.guild_id

        first_name = self.first_name.value.strip()
        last_name = self.last_name.value.strip() if self.last_name.value else ""
        
        # Klasse ermitteln
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

        # Specs
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

        # Vorhandenes Profil prüfen
        existing = await database.get_character(user_id, guild_id)
        image_url = existing["image_url"] if existing else None
        old_msg_id = existing["gallery_message_id"] if existing else None

        bio = None
        armory_url = None
        if self.extra_info.value:
            for line in self.extra_info.value.split("\n"):
                l = line.strip()
                if l.startswith("http"):
                    armory_url = l
                elif l:
                    bio = l

        # Bild aus Upload lesen (falls mitgegeben)
        image_bytes = None
        filename = None
        if self.uploaded_file:
            content_type = self.uploaded_file.content_type or ""
            if content_type.startswith("image/"):
                image_bytes = await self.uploaded_file.read()
                filename = self.uploaded_file.filename

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

        # Galerie posten
        gallery_channel_id = await database.get_gallery_channel(guild_id)
        gallery_status = "Dein Charakterprofil wurde gespeichert!"

        if gallery_channel_id:
            channel = interaction.guild.get_channel(gallery_channel_id)
            if channel:
                # Altes Embed löschen
                if old_msg_id:
                    try:
                        old_msg = await channel.fetch_message(old_msg_id)
                        await old_msg.delete()
                    except Exception:
                        pass

                try:
                    if image_bytes and filename:
                        file_ch = discord.File(io.BytesIO(image_bytes), filename=filename)
                        embed_ch = build_character_embed(interaction.user, char_data, attachment_filename=filename)
                        new_msg = await channel.send(embed=embed_ch, file=file_ch)
                        if new_msg.attachments:
                            image_url = new_msg.attachments[0].url
                            char_data["image_url"] = image_url
                    else:
                        embed_ch = build_character_embed(interaction.user, char_data)
                        new_msg = await channel.send(embed=embed_ch)

                    await database.update_gallery_message_id(user_id, guild_id, new_msg.id)
                    gallery_status += f" Dein Eintrag wurde in {channel.mention} ausgestellt!"
                except discord.Forbidden:
                    gallery_status += f" ⚠️ Der Bot hat keine Schreibrechte in {channel.mention}. Bitte Kanalberechtigungen anpassen!"
                except Exception as e:
                    gallery_status += f" ⚠️ Fehler beim Posten in die Galerie: {e}"
            else:
                gallery_status += " (Hinweis: Galerie-Kanal nicht gefunden. Bitte `/galerie_setup` ausführen)."

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

        embed_preview = build_character_embed(interaction.user, char_data)
        await interaction.followup.send(content=f"✅ **{gallery_status}**", embed=embed_preview, ephemeral=True)


@bot.event
async def on_ready():
    await database.init_db()
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            await bot.tree.sync(guild=guild)
        except Exception as e:
            print(f"Fehler bei Guild-Sync: {e}")
    try:
        await bot.tree.sync()
        print(f"Eingeloggt als {bot.user} | Commands synchronisiert.")
    except Exception as e:
        print(f"Fehler bei Global-Sync: {e}")


# Befehl: In einem Rutsch Charakter eintragen
@bot.tree.command(name="charakter_eintragen", description="Trage deinen WoW Main ein: Bild anhängen & Popup ausfüllen")
@app_commands.describe(bild="Pflichtfeld: Klicke hier oder ziehe deinen Screenshot direkt rein")
async def charakter_eintragen(interaction: discord.Interaction, bild: discord.Attachment):
    # Öffnet sofort das Popup-Fenster und nimmt die angehängte Datei mit!
    modal = CharacterModal(uploaded_file=bild)
    await interaction.response.send_modal(modal)


# Befehl: Profil ansehen
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


# Befehl: Charakter löschen
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


# Befehl: Galerie-Setup (Admin)
@bot.tree.command(name="galerie_setup", description="Admin: Legt den Kanal für die Main-Galerie fest")
@app_commands.describe(channel="Der Kanal, in dem die Main-Charaktere ausgestellt werden")
@app_commands.default_permissions(administrator=True)
async def galerie_setup(interaction: discord.Interaction, channel: discord.TextChannel):
    await database.set_gallery_channel(interaction.guild_id, channel.id)
    await interaction.response.send_message(f"✅ Main-Galerie Kanal wurde auf {channel.mention} gesetzt! Ab jetzt werden Charaktere dort automatisch gepostet und gepflegt.", ephemeral=True)


if __name__ == "__main__":
    if not TOKEN:
        print("FEHLER: Bitte erstelle eine .env-Datei mit DISCORD_TOKEN=dein_bot_token")
        exit(1)
    bot.run(TOKEN)
