import discord
import easyocr
import os
import json
import csv
from datetime import datetime
from upload import upload_to_github

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

            try:
                reader = easyocr.Reader(['en'], gpu=False)
                results = reader.readtext(filename, detail=0)
            except Exception as e:
                await message.channel.send("❌ OCR failed.")
                return

            players, powers, levels = [], [], []
            for line in results:
                line = line.strip()
                if "M" in line:
                    try:
                        powers.append(float(line.split("M")[0].split()[-1]))
                    except: continue
                elif "Lv." in line:
                    try:
                        levels.append(int(line.split("Lv.")[-1].strip().split()[0]))
                    except: continue
                else:
                    name = line.upper()
                    if name and name not in players:
                        players.append(name)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            all_data = load_all_data()
            all_data[timestamp] = {
                "players": players,
                "powers": powers,
                "levels": levels
            }
            save_all_data(all_data)

            csv_filename = f"analysis_{timestamp.replace(':','-').replace(' ', '_')}.csv"
            csv_path = os.path.join(IMAGE_FOLDER, csv_filename)
            with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Player', 'Power (M)', 'Village Level'])
                for i in range(max(len(players), len(powers), len(levels))):
                    writer.writerow([
                        players[i] if i < len(players) else "Unknown",
                        powers[i] if i < len(powers) else "Unknown",
                        levels[i] if i < len(levels) else "Unknown"
                    ])

            # ✅ رفع الملفات للمسارات الصحيحة:
            upload_to_github(filename, f"upload/{os.path.basename(filename)}")
            upload_to_github(DATA_FILE, "data.json")
            upload_to_github(csv_path, f"{csv_filename}")

            await message.channel.send(
                f"📊 Done! Found `{len(players)}` players.\n📎 `{csv_filename}` attached.",
                file=discord.File(csv_path)
            )
        else:
            await message.channel.send("⚠️ Type `dab` first before uploading an image.")

client.run(TOKEN)
