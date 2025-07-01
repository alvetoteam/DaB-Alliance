# bot.py

import discord
import os
from datetime import datetime
from ezy import (
    load_all_data,
    save_all_data,
    analyze_image,
    save_csv,
    upload_to_github
)

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

pending_users = set()

@client.event
async def on_ready():
    print(f'✅ Bot is ready as {client.user}')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    content = message.content.lower()

    if content == 'dab help':
        await message.channel.send(
            "**KSA DaB OCR Bot Help**\n"
            "`dab` - Start scan (then upload image)\n"
            "`sdab` - Show all saved data\n"
            "`xdab` - Shutdown bot"
        )
        return

    if content == 'xdab':
        await message.channel.send("Shutting down... 🛑")
        await client.close()
        return

    if content == 'sdab':
        data = load_all_data()
        if not data:
            await message.channel.send("No data found.")
            return
        reply = "**📂 Saved Player Data:**\n"
        for ts, entry in data.items():
            reply += f"🕒 `{ts}`\n"
            for i in range(len(entry['players'])):
                name = entry['players'][i]
                power = entry['powers'][i] if i < len(entry['powers']) else "?"
                level = entry['levels'][i] if i < len(entry['levels']) else "?"
                reply += f"• `{name}` | `{power}M` | `Lv.{level}`\n"
            reply += "\n"
        await message.channel.send(reply)
        return

    if content == 'dab':
        pending_users.add(user_id)
        await message.channel.send("📥 Please upload an image now.")
        return

    if message.attachments and user_id in pending_users:
        pending_users.remove(user_id)
        await message.channel.send("✅ Image received, analyzing...")

        image = message.attachments[0]
        filename = os.path.join("images", image.filename)
        await image.save(filename)
        print(f"💾 Saved image to {filename}")

        try:
            players, powers, levels, _ = analyze_image(filename)
        except Exception as e:
            print("❌ OCR failed:", e)
            await message.channel.send("❌ OCR failed to process image.")
            return

        print("👥 Players:", players)
        print("💪 Powers:", powers)
        print("🏘️ Levels:", levels)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_data = load_all_data()
        all_data[timestamp] = {
            "players": players,
            "powers": powers,
            "levels": levels
        }
        save_all_data(all_data)
        print("📁 Saved data to JSON.")

        csv_path, csv_filename = save_csv(players, powers, levels, timestamp)
        print("🧾 CSV written:", csv_filename)

        # رفع الملفات
        upload_to_github("data.json", f"uploads/data.json")
        upload_to_github(csv_path, f"uploads/{csv_filename}")
        upload_to_github(filename, f"uploads/{os.path.basename(filename)}")

        await message.channel.send(
            f"📊 Analysis complete. Found {len(players)} players.\n📎 Attached CSV: `{csv_filename}`",
            file=discord.File(csv_path)
        )

    elif message.attachments:
        await message.channel.send("⚠️ Please type `dab` before uploading an image.")

client.run(TOKEN)
