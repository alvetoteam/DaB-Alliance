import discord
import easyocr
import os
import json
from datetime import datetime

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# المستخدمين اللي كتبوا dab وينتظرون يرفعون صورة
pending_users = set()

# تأكد أن مجلد الصور موجود
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# تحميل كل البيانات من JSON
def load_all_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

# حفظ البيانات إلى JSON
def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()
    user_id = message.author.id

    if content == 'dab help':
        help_msg = (
            "**KSA DaB alliance OCR Bot Help**\n"
            "`dab` - Start analysis process. Upload an image after this command.\n"
            "`sdab` - Show all saved player data.\n"
            "`xdab` - Shutdown the bot.\n\n"
            "_Note: Powered by KSA – DaB alliance (vlaibee)_"
        )
        await message.channel.send(help_msg)
        return

    if content == 'xdab':
        await message.channel.send("⏹️ Bot is shutting down... Bye!")
        await client.close()
        return

    if content == 'sdab':
        data = load_all_data()
        if not data:
            await message.channel.send("📂 No player data available.")
            return

        reply = "**📂 All saved player data:**\n"
        for ts, info in data.items():
            reply += f"🕒 `{ts}`\n"
            players = info.get('players', [])
            powers = info.get('powers', [])
            levels = info.get('levels', [])
            for i in range(len(players)):
                p = players[i] if i < len(players) else "Unknown"
                po = powers[i] if i < len(powers) else "Unknown"
                lv = levels[i] if i < len(levels) else "Unknown"
                reply += f"• Player: `{p}` | Power: `{po}M` | Village Level: `Lv.{lv}`\n"
            reply += "\n"
        reply += "\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_"
        await message.channel.send(reply)
        return

    if content == 'dab':
        pending_users.add(user_id)
        await message.channel.send("📥 Got it! Now please upload an image.")
        return

    # تحليل الصورة بعد أمر dab
    if message.attachments:
        if user_id in pending_users:
            pending_users.remove(user_id)
            await message.channel.send("✅ Image received... Analyzing now 🔍")

            start_time = datetime.now()
            attachment = message.attachments[0]
            file_path = os.path.join(IMAGE_FOLDER, attachment.filename)
            await attachment.save(file_path)

            reader = easyocr.Reader(['en'])
            results = reader.readtext(file_path, detail=0)

            try:
                os.remove(file_path)
            except:
                pass

            players, powers, levels = [], [], []

            for line in results:
                line = line.strip()
                if 'M' in line:
                    try:
                        part = line.split('M')[0].strip().split()[-1]
                        powers.append(float(part))
                    except:
                        continue
                elif 'Lv.' in line:
                    try:
                        part = line.split('Lv.')[-1].strip().split()[0]
                        levels.append(int(part))
                    except:
                        continue
                else:
                    if line and line.upper() not in players:
                        players.append(line.upper())

            all_data = load_all_data()
            timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")

            all_data[timestamp] = {
                'players': players,
                'powers': powers,
                'levels': levels
            }

            save_all_data(all_data)

            elapsed = (datetime.now() - start_time).total_seconds()

            reply = f"📊 Analysis Complete in {elapsed:.2f} seconds.\n"
            reply += f"Found {len(players)} players.\n\n"
            reply += "Players | Power (M) | Village Level\n"
            reply += "--- | --- | ---\n"

            max_len = max(len(players), len(powers), len(levels))
            for i in range(max_len):
                p = players[i] if i < len(players) else "Unknown"
                po = powers[i] if i < len(powers) else "Unknown"
                lv = levels[i] if i < len(levels) else "Unknown"
                reply += f"{p} | {po} | Lv.{lv}\n"

            reply += "\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_"
            await message.channel.send(reply)
        else:
            await message.channel.send("⚠️ Please type `dab` first before uploading an image.")

client.run(TOKEN)
