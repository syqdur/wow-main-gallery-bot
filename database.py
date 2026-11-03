import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "gallery.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Settings table for guild gallery channels
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                gallery_channel_id INTEGER
            )
        """)
        # Character profiles table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS characters (
                user_id INTEGER,
                guild_id INTEGER,
                first_name TEXT NOT NULL,
                last_name TEXT,
                char_class TEXT NOT NULL,
                main_spec TEXT NOT NULL,
                dual_spec TEXT,
                race TEXT,
                image_url TEXT,
                armory_url TEXT,
                bio TEXT,
                gallery_message_id INTEGER,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, guild_id)
            )
        """)
        await db.commit()

async def set_gallery_channel(guild_id: int, channel_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO guild_settings (guild_id, gallery_channel_id)
            VALUES (?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET gallery_channel_id = excluded.gallery_channel_id
        """, (guild_id, channel_id))
        await db.commit()

async def get_gallery_channel(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT gallery_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def save_character(user_id: int, guild_id: int, first_name: str, last_name: str, 
                         char_class: str, main_spec: str, dual_spec: str, race: str, 
                         image_url: str, armory_url: str, bio: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO characters (user_id, guild_id, first_name, last_name, char_class, 
                                    main_spec, dual_spec, race, image_url, armory_url, bio, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, guild_id) DO UPDATE SET
                first_name = excluded.first_name,
                last_name = excluded.last_name,
                char_class = excluded.char_class,
                main_spec = excluded.main_spec,
                dual_spec = excluded.dual_spec,
                race = excluded.race,
                image_url = excluded.image_url,
                armory_url = excluded.armory_url,
                bio = excluded.bio,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, guild_id, first_name, last_name, char_class, main_spec, dual_spec, race, image_url, armory_url, bio))
        await db.commit()

async def update_gallery_message_id(user_id: int, guild_id: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE characters SET gallery_message_id = ?
            WHERE user_id = ? AND guild_id = ?
        """, (message_id, user_id, guild_id))
        await db.commit()

async def get_character(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM characters WHERE user_id = ? AND guild_id = ?
        """, (user_id, guild_id)) as cursor:
            return await cursor.fetchone()

async def delete_character(user_id: int, guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT gallery_message_id FROM characters WHERE user_id = ? AND guild_id = ?", (user_id, guild_id)) as cursor:
            row = await cursor.fetchone()
            msg_id = row[0] if row else None

        await db.execute("DELETE FROM characters WHERE user_id = ? AND guild_id = ?", (user_id, guild_id))
        await db.commit()
        return msg_id

async def list_guild_characters(guild_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT * FROM characters WHERE guild_id = ? ORDER BY first_name ASC
        """, (guild_id,)) as cursor:
            return await cursor.fetchall()
