import discord
import pytesseract
from PIL import Image
import io
import os
import json
import time

TOKEN = os.getenv('DISCORD_BOT_TOKEN')

DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images/'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# تأكد من وجود مجلد الصور
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# تحميل البيانات السابقة
def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# حفظ البيانات
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# استخراج البيانات من الصورة
def extract_data_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    players = []
    for line in lines:
        name = None
        power = None
        level = None

        words = line.split()
        for i, word in enumerate(words):
            if word.upper() == "LV." and i + 1 < len(words):
                try:
                    level = int(words[i + 1])
                except:
                    pass
            elif "M" in word:
                try:
                    power = float(word.replace("M", ""))
                except:
                    pass
            elif name is None:
                name = words[0]

        if name and power and level:
            players.append({
                "name": name.upper(),
                "power": power,
                "level": level
            })

    return players

# مقارنة البيانات
def compare_players(new_players, old_data):
    changes = []
    duplicates = []
    updated_data = old_data.copy()

    for p in new_players:
        name = p['name']
        if name in old_data:
            old = old_data[name]
            diff_power = p['power'] - old['power']
            diff_level = p['level'] - old['level']

            if diff_power != 0 or diff_level != 0:
                changes.append({
                    'name': name,
                    'old_power': old['power'],
                    'new_power': p['power'],
                    'old_level': old['level'],
                    'new_level': p['level']
                })
            duplicates.append(name)
        updated_data[name] = {'power': p['power'], 'level': p['level']}

    return changes, duplicates, updated_data

@client.event
async def on_ready():
    print(f"✅ Bot is ready as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    # أوامر خاصة
    if content == "dab help":
        await message.channel.send(
            "**🛠 Available Commands:**\n"
            "`dab` → Start analysis by uploading an image.\n"
            "`sdab` → Show stored player data in plain text.\n"
            "`xdab` → Shut down the bot (admin only).\n"
            "\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_"
        )
        return

    if content == "xdab":
        await message.channel.send("👋 Shutting down the bot...\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        await client.close()
        return

    if content == "sdab":
        data = load_data()
        if not data:
            await message.channel.send("📂 No player data available.\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        else:
            result = "**📋 Stored Player Data:**\n"
            for name, stats in data.items():
                result += f"- {name}: Power: {stats['power']}M | Level: {stats['level']}\n"
            await message.channel.send(result + "\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        return

    if content == "dab":
        await message.channel.send("📥 Please upload an image now for analysis.")
        return

    if message.content.startswith("dab") and message.attachments:
        start_time = time.time()

        await message.channel.send("✅ Image received... Analyzing now 🔍")

        attachment = message.attachments[0]
        image_path = os.path.join(IMAGE_FOLDER, attachment.filename)
        await attachment.save(image_path)

        new_players = extract_data_from_image(image_path)
        old_data = load_data()
        changes, duplicates, updated_data = compare_players(new_players, old_data)
        save_data(updated_data)

        if not new_players:
            await message.channel.send("⚠️ No valid player data found in the image.")
            return

        if changes:
            table = "**📊 Update Results:**\n```\n"
            for c in changes:
                table += (
                    f"{c['name']} | Power: {c['old_power']}M → {c['new_power']}M | "
                    f"Lv: {c['old_level']} → {c['new_level']}\n"
                )
            table += "```\n"
        else:
            table = "📊 Update Results:\n```\n✅ No changes detected.\n```"

        end_time = time.time()
        duration = round(end_time - start_time, 2)
        table += f"\n⏱ Analysis completed in {duration} seconds."
        table += "\n\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_"

        await message.channel.send(table)

client.run(TOKEN)
