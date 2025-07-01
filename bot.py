import discord
import easyocr
import os
import json
import csv
import asyncio
from datetime import datetime

TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # ضع التوكن الخاص بك في متغير بيئة
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
            "**🧠 KSA DaB OCR Bot Help**\n"
            "`dab` - Start scan (then upload image[s])\n"
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
            await message.channel.send("📂 No data found.")
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
        await message.channel.send("📥 Please upload up to 10 images now.")
        return

    if message.attachments and user_id in pending_users:
        pending_users.remove(user_id)
        await message.channel.send("✅ Images received, analyzing...")

        all_results = []
        reader = easyocr.Reader(['en'], gpu=False)

        for attachment in message.attachments[:10]:
            filename = os.path.join(IMAGE_FOLDER, attachment.filename)
            await attachment.save(filename)

            try:
                results = await asyncio.to_thread(reader.readtext, filename, detail=0)
            except Exception as e:
                await message.channel.send(f"⚠️ Error reading `{attachment.filename}`: {e}")
                continue
            finally:
                try:
                    os.remove(filename)
                except:
                    pass

            # تنظيف البيانات
            filtered = [
                line.strip() for line in results
                if line.strip() and all(x not in line.lower() for x in ["day", "hour", "minute", "ago"])
            ]

            # تجميع الأسماء والقوة والمستوى
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

                all_results.append((name, power, level))
                i += 3

        if not all_results:
            await message.channel.send("❌ No valid player data found.")
            return

        # حفظ البيانات
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_data = load_all_data()

        players = [x[0] for x in all_results]
        powers = [x[1] for x in all_results]
        levels = [x[2] for x in all_results]

        all_data[timestamp] = {
            "players": players,
            "powers": powers,
            "levels": levels
        }

        save_all_data(all_data)

        # حفظ CSV
        csv_filename = f"analysis_{timestamp.replace(':', '-').replace(' ', '_')}.csv"
        csv_path = os.path.join(IMAGE_FOLDER, csv_filename)
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Player', 'Power (M)', 'Village Level'])
            for p in all_results:
                writer.writerow(p)

        # بناء الجدول داخل الديسكورد
        table = "📊 **Analysis Results**\n"
        table += "**Player** | **Power (M)** | **Lv.**\n"
        table += "--- | --- | ---\n"
        for name, power, level in all_results:
            table += f"{name} | {power} | Lv.{level}\n"

        await message.channel.send(table)
        await message.channel.send(f"📎 Attached CSV file: `{csv_filename}`", file=discord.File(csv_path))

    elif message.attachments:
        await message.channel.send("⚠️ Please use `dab` first before uploading image(s).")

client.run(TOKEN)
