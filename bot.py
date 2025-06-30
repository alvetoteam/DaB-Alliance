import discord
import pytesseract
from PIL import Image
import io
import os
import json
from datetime import datetime

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Load previous data
def load_player_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save data
def save_player_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Extract from image
def extract_players_from_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(image)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    players = {}
    for line in lines:
        words = line.split()
        if len(words) >= 3:
            name = words[0].upper()
            try:
                power = int(words[1].replace(',', ''))
                village = int(words[2])
                players[name] = {'power': power, 'village': village}
            except:
                continue
    return players, lines

# Compare
def compare_players(old_data, new_data):
    added = []
    updated = []
    unchanged = []

    for name, stats in new_data.items():
        if name not in old_data:
            added.append((name, stats))
        else:
            old_stats = old_data[name]
            if stats != old_stats:
                updated.append((name, old_stats, stats))
            else:
                unchanged.append(name)

    result = "📊 Update Results:\n"
    if added:
        result += "\n🟢 **New Players:**\n"
        for name, stats in added:
            result += f"- {name}: Power {stats['power']}, Village {stats['village']}\n"
    if updated:
        result += "\n🟡 **Updated Players:**\n"
        for name, old, new in updated:
            result += (
                f"- {name}: Power {old['power']} → {new['power']}, "
                f"Village {old['village']} → {new['village']}\n"
            )
    if not added and not updated:
        result += "✅ No changes detected."

    return result

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    if content == "dab":
        await message.channel.send("📥 Upload an image now for analysis.")
        await message.channel.send("📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")

    elif content == "dab help":
        await message.channel.send(
            "**🛠️ Dab Bot Help**\n"
            "`dab` - Start analysis.\n"
            "`sdab` - Show stored data.\n"
            "`xdab` - Shut down bot.\n"
            "`dab help` - Show this message."
        )
        await message.channel.send("📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")

    elif content == "sdab":
        data = load_player_data()
        if not data:
            await message.channel.send("📂 No player data available.")
        else:
            rows = []
            for name, stats in data.items():
                rows.append(f"{name}: Power {stats['power']}, Village {stats['village']}")
            await message.channel.send("📊 Current Player Data:\n```\n" + "\n".join(rows) + "\n```")
        await message.channel.send("📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")

    elif content == "xdab":
        await message.channel.send("Shutting down... 🔌")
        await message.channel.send("📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        await client.close()

    elif message.attachments:
        await message.channel.send("✅ Image received. Analyzing... 🔍")
        image_bytes = await message.attachments[0].read()
        new_data, lines = extract_players_from_image(image_bytes)
        old_data = load_player_data()
        result = compare_players(old_data, new_data)
        save_player_data({**old_data, **new_data})
        await message.channel.send(result)
        await message.channel.send("📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")

client.run(TOKEN)
