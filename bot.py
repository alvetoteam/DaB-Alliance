import discord
import pytesseract
from PIL import Image
import io
import os
import json
import time
from datetime import datetime

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images/'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Ensure image folder exists
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Load previous players from file
def load_previous_players():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save updated players list to file
def save_players(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Extract data from image using OCR
def extract_data_from_image(image_path):
    image = Image.open(image_path)
    text = pytesseract.image_to_string(image)

    cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
    players = {}

    for line in cleaned_lines:
        words = line.split()
        if len(words) >= 3:
            name = words[0].upper()
            power = None
            level = None

            for i, word in enumerate(words):
                if 'M' in word:
                    try:
                        power = float(word.replace('M', ''))
                    except:
                        pass
                if 'Lv.' in word:
                    try:
                        level = int(word.replace('Lv.', ''))
                    except:
                        pass

            if name and power and level is not None:
                players[name] = {
                    'power': power,
                    'level': level,
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
                }
    return players

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}')
    print('Ready for dab commands.')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    if content == 'dab':
        await message.channel.send("📥 Please upload an image for analysis.")

    elif content == 'xdab':
        await message.channel.send("🛑 Bot is shutting down...\n\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        await client.close()

    elif content == 'dab data':
        data = load_previous_players()
        if not data:
            await message.channel.send("📂 No player data available.\n\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        else:
            msg = "**📄 Stored Player Data:**\n"
            for name, info in data.items():
                msg += f"- {name}: Power {info['power']}M | Lv. {info['level']} | 🕒 {info['timestamp']}\n"
            await message.channel.send(msg + "\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")

    elif message.attachments and any(msg.content.lower().startswith(cmd) for cmd in ['dab']):
        await message.channel.send("✅ Image received... Analyzing now 🔍")
        start = time.time()

        attachment = message.attachments[0]
        file_path = os.path.join(IMAGE_FOLDER, attachment.filename)
        await attachment.save(file_path)

        new_data = extract_data_from_image(file_path)
        previous_data = load_previous_players()

        changes = []
        for name, info in new_data.items():
            if name in previous_data:
                prev = previous_data[name]
                diff_power = info['power'] - prev['power']
                diff_lvl = info['level'] - prev['level']

                if diff_power != 0 or diff_lvl != 0:
                    changes.append(
                        f"🔁 {name} | 🏠 Lv. {prev['level']} → {info['level']} | 💪 {prev['power']}M → {info['power']}M"
                    )
            else:
                changes.append(
                    f"🆕 {name} | 🏠 Lv. {info['level']} | 💪 {info['power']}M"
                )

            # Update or add player
            previous_data[name] = info

        save_players(previous_data)

        if changes:
            result = "📊 Update Results:\n" + "\n".join(changes)
        else:
            result = "📊 Update Results:\n```\n✅ No changes detected.\n```"

        end = time.time()
        duration = round(end - start, 2)

        result += f"\n⏱️ Analysis completed in {duration} sec."
        result += "\n\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_"
        await message.channel.send(result)

client.run(TOKEN)
