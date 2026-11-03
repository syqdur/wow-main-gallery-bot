import os
import io
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

import database
from helpers import build_character_embed, WOW_CLASSES

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
# Message Content Intent falls vorhanden, sonst Fallback
try:
    intents.message_content = True
except Exception:
    pass

bot = commands.Bot(command_prefix="!", intents=intents)

async def post_to_gallery(guild: discord.Guild, user: discord.User | discord.Member, char_data: dict, image_bytes: bytes = None, filename: str = None):
    """Hilfsfunktion: Postet oder aktualisiert die Karte in der Galerie"""
    gallery_channel_id = await database.get_gallery_channel(guild.id)
    if not gallery_channel_id:
        return "⚠️ Es ist noch kein Galerie-Kanal eingerichtet. Bitte einrichten mit `/galerie_setup`."

    channel = guild.get_channel(gallery_channel_id)
    if not channel:
        return "⚠️ Der konfigurierte Galerie-Kanal wurde nicht gefunden."

    existing = await database.get_character(user.id, guild.id)
    old_msg_id = existing["gallery_message_id"] if existing else None

    # Altes Embed im Kanal löschen (damit keine Duplikate entstehen)
    if old_msg_id:
        try:
            old_msg = await channel.fetch_message(old_msg_id)
            await old_msg.delete()
        except Exception:
            pass

    try:
        if image_bytes and filename:
            file_ch = discord.File(io.BytesIO(image_bytes), filename=filename)
            embed_ch = build_character_embed(user, char_data, attachment_filename=filename)
            new_msg = await channel.send(embed=embed_ch, file=file_ch)
            if new_msg.attachments:
                char_data["image_url"] = new_msg.attachments[0].url
        else:
            embed_ch = build_character_embed(user, char_data)
            new_msg = await channel.send(embed=embed_ch)

        # In DB speichern
        await database.save_character(
            user_id=user.id,
            guild_id=guild.id,
            first_name=char_data["first_name"],
            last_name=char_data["last_name"],
            char_class=char_data["char_class"],
            main_spec=char_data["main_spec"],
            dual_spec=char_data["dual_spec"],
            race=char_data["race"],
            image_url=char_data.get("image_url"),
            armory_url=char_data.get("armory_url"),
            bio=char_data.get("bio")
        )
        await database.update_gallery_message_id(user.id, guild.id, new_msg.id)
        return f"✅ Dein Charakter wurde erfolgreich in {channel.mention} ausgestellt!"
    except discord.Forbidden:
        return f"⚠️ Der Bot hat keine Schreibrechte in {channel.mention}. Bitte Kanalrechte prüfen!"
    except Exception as e:
        return f"⚠️ Fehler beim Ausstellen in der Galerie: {e}"


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
        placeholder="Optional: Kurze Bio oder Arsenal-Link",
        max_length=300,
        required=False
    )

    def __init__(self, uploaded_file: discord.Attachment = None):
        super().__init__()
        self.uploaded_file = uploaded_file

    async def on_submit(self, interaction: discord.Interaction):
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
        existing = await database.get_character(interaction.user.id, interaction.guild_id)
        image_url = existing["image_url"] if existing else None
        
        bio = None
        armory_url = None
        if self.extra_info.value:
            for line in self.extra_info.value.split("\n"):
                l = line.strip()
                if l.startswith("http"):
                    armory_url = l
                elif l:
                    bio = l

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

        # Fall 1: Bild wurde direkt im Befehl mitgegeben
        if self.uploaded_file:
            await interaction.response.defer(ephemeral=True)
            img_bytes = await self.uploaded_file.read()
            status = await post_to_gallery(interaction.guild, interaction.user, char_data, img_bytes, self.uploaded_file.filename)
            embed_prev = build_character_embed(interaction.user, char_data)
            await interaction.followup.send(status, embed=embed_prev, ephemeral=True)
            return

        # Fall 2: In einem Rutsch - Jetzt direkt nach dem Bild im Chat fragen!
        await interaction.response.send_message(
            f"📸 **Perfekt, {interaction.user.mention}!**\n"
            f"Lade jetzt bitte deinen **Screenshot / Bild** hier in den Chat hoch (einfach Datei reinziehen oder auswählen)!\n"
            f"*(Oder schreibe `skip`, um die Karte vorerst ohne Bild zu erstellen)*"
        )
        prompt_message = await interaction.original_response()

        def check(m: discord.Message):
            return m.author.id == interaction.user.id and m.channel.id == interaction.channel.id

        try:
            msg = await bot.wait_for('message', check=check, timeout=120.0)
            
            image_bytes = None
            filename = None

            if msg.attachments:
                att = msg.attachments[0]
                if (att.content_type or "").startswith("image/"):
                    image_bytes = await att.read()
                    filename = att.filename

            # Benutzer-Upload-Nachricht sauber wegräumen
            try:
                await msg.delete()
            except Exception:
                pass

            # Prompt-Nachricht wegräumen
            try:
                await prompt_message.delete()
            except Exception:
                pass

            status = await post_to_gallery(interaction.guild, interaction.user, char_data, image_bytes, filename)
            embed_prev = build_character_embed(interaction.user, char_data)
            await interaction.channel.send(f"{interaction.user.mention} {status}", embed=embed_prev, delete_after=15)

        except asyncio.TimeoutError:
            # Falls der Nutzer nach 2 Minuten kein Bild gesendet hat:
            try:
                await prompt_message.delete()
            except Exception:
                pass
            status = await post_to_gallery(interaction.guild, interaction.user, char_data)
            await interaction.channel.send(f"{interaction.user.mention} Zeit abgelaufen. {status} *(Ein Bild kannst du jederzeit nachreichen)*", delete_after=15)


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


# Befehl: Charakter eintragen
@bot.tree.command(name="charakter_eintragen", description="Öffnet das Formular für deinen WoW Main-Charakter")
@app_commands.describe(bild="Optional: Du kannst das Bild auch direkt hier anhängen")
async def charakter_eintragen(interaction: discord.Interaction, bild: discord.Attachment = None):
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
