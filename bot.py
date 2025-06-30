import discord
import pytesseract
from PIL import Image
import io
import os
import json
import time

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def load_previous_players():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('players', []))
    except FileNotFoundError:
        return set()

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

    if message.content.lower() == "dab":
        await message.channel.send("📥 Please upload an image now for analysis.")

    elif message.attachments:
        await message.channel.send("✅ Image received... Analyzing now 🔍")

        attachment = message.attachments[0]
        file_path = f"images/{attachment.filename}"
        await attachment.save(file_path)
        print(f"Image saved to {file_path}")

        start_time = time.time()

        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)
        print(f"Extracted text:\n{text}")

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

        all_players = previous_players.union(new_players)
        save_players(all_players)

        end_time = time.time()
        elapsed = end_time - start_time

        response = "📄 **OCR Result:**\n```\n" + "\n".join(cleaned_lines) + "\n```"

        if duplicates:
            response += f"\n⚠️ Duplicate players found: {', '.join(duplicates)}"

        await message.channel.send(response)

        if not new_players:
            await message.channel.send("📊 Update Results:\n✅ No changes detected.")
        else:
            await message.channel.send(f"📊 Update Results:\n✅ New players added: {', '.join(new_players)}")

        await message.channel.send(f"⏱️ Analysis took {elapsed:.2f} seconds.")
        await message.channel.send("\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")

client.run(TOKEN)
