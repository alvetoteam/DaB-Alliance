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

bot_active = True

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

# Extract text data from image using OCR
def extract_data_from_image(file_path):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image)
    # Clean and split lines
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}!')

@client.event
async def on_message(message):
    global bot_active

    if message.author.bot:
        return

    msg = message.content.lower()

    if msg == "xdab":
        if not bot_active:
            await message.channel.send("🤖 The bot is already inactive.")
            return
        bot_active = False
        await message.channel.send("🛑 Bot is now inactive. Use `dab` to activate it again.\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        return

    if msg == "dab":
        if bot_active:
            await message.channel.send("🤖 The bot is already active.")
            return
        bot_active = True
        await message.channel.send("✅ Bot is now active again.\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        return

    if msg == "sdab":
        status = "active" if bot_active else "inactive"
        await message.channel.send(f"ℹ️ Bot status: **{status}**.\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        return

    if msg == "dab data":
        players = load_previous_players()
        if not players:
            await message.channel.send("📂 No player data available.\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        else:
            players_list = "\n".join(sorted(players))
            await message.channel.send(f"📂 Player Data:\n```\n{players_list}\n```\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        return

    if not bot_active:
        return

    # If message contains attachments (images)
    if message.attachments:
        await message.channel.send("✅ Image received... Analyzing now 🔍")

        attachment = message.attachments[0]
        os.makedirs("images", exist_ok=True)
        file_path = f"images/{attachment.filename}"
        await attachment.save(file_path)

        start_time = time.time()

        lines = extract_data_from_image(file_path)

        previous_players = load_previous_players()
        new_players = set()
        duplicates = []

        # Example: assume first word in line is player name in uppercase
        for line in lines:
            words = line.split()
            if words:
                name = words[0].upper()
                if name in previous_players:
                    duplicates.append(name)
                else:
                    new_players.add(name)

        all_players = previous_players.union(new_players)
        save_players(all_players)

        elapsed = time.time() - start_time

        response = "📄 **OCR Result:**\n```\n" + "\n".join(lines) + "\n```"

        if duplicates:
            response += f"\n⚠️ Duplicate players found: {', '.join(duplicates)}"

        response += f"\n⏱ Analysis took {elapsed:.2f} seconds."
        response += "\n\n😏 Don’t forget to thank KSA - DaB alliance (vlaibee)"

        await message.channel.send(response)

client.run(TOKEN)
