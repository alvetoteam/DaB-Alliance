import discord
import pytesseract
from PIL import Image
import io
import os

TOKEN = os.getenv('DISCORD_BOT_TOKEN')  # توكن البوت من متغير البيئة

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith('!تحليل') and message.attachments:
        attachment = message.attachments[0]
        img_bytes = await attachment.read()
        image = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(image)

        # تنظيف النص
        cleaned = "\n".join([line.strip() for line in text.splitlines() if line.strip()])

        await message.channel.send(f"📄 **OCR Result:**\n```\n{cleaned}\n```")

client.run(TOKEN)