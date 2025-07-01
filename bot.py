import discord
import easyocr
import os
import json
import csv
from datetime import datetime

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

pending_users = set()

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

def load_all_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

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

    if message.attachments:
        if user_id in pending_users:
            pending_users.remove(user_id)
            await message.channel.send("✅ Image received, analyzing...")

            image = message.attachments[0]
            filename = os.path.join(IMAGE_FOLDER, image.filename)
            await image.save(filename)

            reader = easyocr.Reader(['en'], gpu=False)
            print("📷 Running OCR...")
            results = reader.readtext(filename, detail=0)
            print("📋 OCR Results:")
            for r in results:
                print("👉", r)

            try:
                os.remove(filename)
            except:
                pass

            # Filter unwanted lines
            filtered = [
                line.strip() for line in results
                if line.strip()
                and 'day' not in line.lower()
                and 'hour' not in line.lower()
                and 'minute' not in line.lower()
                and 'ago' not in line.lower()
            ]

            players, powers, levels = [], [], []

            i = 0
            while i < len(filtered):
                name = filtered[i].upper()
                power = "Unknown"
                level = "Unknown"

                if i + 1 < len(filtered) and 'M' in filtered[i + 1]:
                    try:
                        power = float(filtered[i + 1].split("M")[0].split()[-1])
                    except:
                        pass

                if i + 2 < len(filtered) and 'Lv.' in filtered[i + 2]:
                    try:
                        level = int(filtered[i + 2].split("Lv.")[-1].strip().split()[0])
                    except:
                        pass

                players.append(name)
                powers.append(power)
                levels.append(level)
                i += 3

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            all_data = load_all_data()
            all_data[timestamp] = {
                "players": players,
                "powers": powers,
                "levels": levels
            }

            save_all_data(all_data)

            # Save to CSV
            csv_filename = f"analysis_{timestamp.replace(':', '-').replace(' ', '_')}.csv"
            csv_path = os.path.join(IMAGE_FOLDER, csv_filename)
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Player', 'Power (M)', 'Village Level'])
                for i in range(len(players)):
                    writer.writerow([
                        players[i],
                        powers[i] if i < len(powers) else "Unknown",
                        levels[i] if i < len(levels) else "Unknown"
                    ])

            msg = f"📊 Analysis done. Found {len(players)} players.\n"
            msg += f"📎 Attached CSV file: `{csv_filename}`\n"
            await message.channel.send(msg, file=discord.File(csv_path))
        else:
            await message.channel.send("⚠️ Please type `dab` before uploading an image.")

client.run(TOKEN)
