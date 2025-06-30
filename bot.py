import discord
import pytesseract
from PIL import Image
import io
import os
import json
from cryptography.fernet import Fernet

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'
KEY_FILE = 'secret.key'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

def generate_key():
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, 'wb') as f:
            f.write(key)

def load_key():
    with open(KEY_FILE, 'rb') as f:
        return f.read()

def load_previous_players():
    if not os.path.exists(DATA_FILE):
        return {}

    fernet = Fernet(load_key())
    with open(DATA_FILE, 'rb') as f:
        encrypted_data = f.read()
    try:
        decrypted = fernet.decrypt(encrypted_data)
        return json.loads(decrypted.decode())
    except:
        return {}

def save_players(data):
    fernet = Fernet(load_key())
    encrypted = fernet.encrypt(json.dumps(data).encode())
    with open(DATA_FILE, 'wb') as f:
        f.write(encrypted)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}!')
    await client.change_presence(activity=discord.Game(name="Type 'dab' to start analysis!"))

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.lower() == "dab":
        await message.channel.send("📥 Please upload an image now for analysis.")
        return

    if message.attachments:
        await message.channel.send("✅ Image received... Analyzing now 🔍")
        attachment = message.attachments[0]
        img_bytes = await attachment.read()
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image)

        cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
        new_data = {}
        updates = []
        previous_data = load_previous_players()

        for line in cleaned_lines:
            parts = line.split()
            if len(parts) >= 3:
                name = parts[0].upper()
                try:
                    power = int(parts[1].replace(",", ""))
                    level = int(parts[2])
                except:
                    continue

                if name in previous_data:
                    old = previous_data[name]
                    diff_power = power - old['power']
                    diff_level = level - old['level']
                    updates.append(f"{name}: Power {old['power']} → {power} (Δ {diff_power}), Level {old['level']} → {level} (Δ {diff_level})")
                else:
                    updates.append(f"{name}: New player added. Power {power}, Level {level}")

                new_data[name] = {"power": power, "level": level}

        previous_data.update(new_data)
        save_players(previous_data)

        reply = "\n".join(updates) if updates else "✅ No changes detected."
        await message.channel.send(f"📊 Update Results:\n```\n{reply}\n```\n😏 Don’t forget to thank KSA - DaB alliance (vlaibee)")
        return

generate_key()
client.run(TOKEN)
