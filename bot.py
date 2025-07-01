import discord
import easyocr
import os
import json
import csv
import base64
import requests
from datetime import datetime

# إعدادات
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = "alvetoteam/Dab alliance"
GITHUB_BRANCH = "main"
GITHUB_FOLDER = "uploads"

DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

pending_users = set()

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# تحميل و حفظ البيانات
def load_all_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# رفع ملف إلى GitHub
def upload_to_github(file_path, github_path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    message = f"Upload {github_path}"
    data = {
        "message": message,
        "content": content,
        "branch": GITHUB_BRANCH
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    r = requests.put(url, headers=headers, json=data)
    return r.status_code in [200, 201]

# مقارنة النتائج
def compare_data(new_players, new_powers, new_levels, old_entry):
    diffs = []
    old_players = old_entry.get('players', [])
    old_powers = old_entry.get('powers', [])
    old_levels = old_entry.get('levels', [])

    for i, player in enumerate(new_players):
        if player in old_players:
            old_index = old_players.index(player)
            old_power = old_powers[old_index] if old_index < len(old_powers) else 0
            old_level = old_levels[old_index] if old_index < len(old_levels) else 0
            new_power = new_powers[i] if i < len(new_powers) else 0
            new_level = new_levels[i] if i < len(new_levels) else 0
            power_diff = round(new_power - old_power, 2)
            level_diff = new_level - old_level
            if power_diff != 0 or level_diff != 0:
                diffs.append(f"🔁 `{player}`: Power `{old_power}M → {new_power}M` ({'+' if power_diff>=0 else ''}{power_diff}M), Level `Lv.{old_level} → Lv.{new_level}` ({'+' if level_diff>=0 else ''}{level_diff})")
    return diffs

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
            results = reader.readtext(filename, detail=0)

            players, powers, levels = [], [], []

            for line in results:
                line = line.strip()
                if "M" in line:
                    try:
                        value = float(line.split("M")[0].split()[-1])
                        powers.append(value)
                    except:
                        continue
                elif "Lv." in line:
                    try:
                        value = int(line.split("Lv.")[-1].strip().split()[0])
                        levels.append(value)
                    except:
                        continue
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

            # حفظ CSV
            csv_filename = f"analysis_{timestamp.replace(':','-').replace(' ', '_')}.csv"
            csv_path = os.path.join(IMAGE_FOLDER, csv_filename)
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Player', 'Power (M)', 'Village Level'])
                for i in range(max(len(players), len(powers), len(levels))):
                    name = players[i] if i < len(players) else "Unknown"
                    power = powers[i] if i < len(powers) else "Unknown"
                    level = levels[i] if i < len(levels) else "Unknown"
                    writer.writerow([name, power, level])

            # مقارنة
            latest_key = sorted(all_data.keys())[-2] if len(all_data) >= 2 else None
            diff_msg = ""
            if latest_key:
                diff = compare_data(players, powers, levels, all_data[latest_key])
                if diff:
                    diff_msg = "**📈 Comparison with last scan:**\n" + "\n".join(diff) + "\n\n"
                else:
                    diff_msg = "✅ No changes compared to last scan.\n\n"

            # رفع إلى GitHub
            upload_to_github(DATA_FILE, f"{GITHUB_FOLDER}/data.json")
            upload_to_github(csv_path, f"{GITHUB_FOLDER}/{csv_filename}")
            upload_to_github(filename, f"{GITHUB_FOLDER}/{os.path.basename(filename)}")

            # الرد
            msg = f"📊 Analysis done. Found {len(players)} players.\n"
            msg += diff_msg
            msg += f"📎 CSV: `{csv_filename}` uploaded to GitHub."

            await message.channel.send(msg, file=discord.File(csv_path))
        else:
            await message.channel.send("⚠️ Please type `dab` before uploading an image.")

client.run(TOKEN)
