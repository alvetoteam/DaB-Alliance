# bot.py

# bot.py
import discord
import os
from ezy import upload_to_github

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

pending_users = set()

@client.event
async def on_ready():
    print(f"✅ Bot is ready as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    content = message.content.lower()

    if content == 'dab':
        pending_users.add(user_id)
        await message.channel.send("📥 Please upload an image now.")
        return

    if message.attachments and user_id in pending_users:
        pending_users.remove(user_id)
        image = message.attachments[0]
        filename = os.path.join("images", image.filename)
        await image.save(filename)
        upload_to_github(filename, f"upload{os.path.basename(filename)}")
        await message.channel.send("✅ Image uploaded to GitHub for processing.")
        return

    if message.attachments:
        await message.channel.send("⚠️ Please type `dab` first.")

client.run(TOKEN)
