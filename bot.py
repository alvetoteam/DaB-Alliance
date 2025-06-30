import discord
import pytesseract
from PIL import Image
import io
import os
import json

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Load previous players from file
def load_previous_players():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('players', []))
    except FileNotFoundError:
        return set()

# Save updated players list to file
def save_players(players):
    with open(DATA_FILE, 'w') as f:
        json.dump({'players': list(players)}, f)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('dab') and message.attachments:
        attachment = message.attachments[0]
        img_bytes = await attachment.read()
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image)

        # تنظيف النص
        cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
        new_players = set()
        duplicates = []

        previous_players = load_previous_players()

        for line in cleaned_lines:
            words = line.split()
            if words:
                name = words[0].upper()
                if name in previous_players:
                    duplicates.append(name)
                else:
                    new_players.add(name)

        # تحديث القائمة
        all_players = previous_players.union(new_players)
        save_players(all_players)

        # بناء الرد
        response = "📄 **OCR Result:**\n```\n" + "\n".join(cleaned_lines) + "\n```"

        if duplicates:
            response += f"\n⚠️ Duplicate players found: {', '.join(duplicates)}"

        await message.channel.send(response)

client.run(TOKEN)
