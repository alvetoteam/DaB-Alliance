# -*- coding: utf-8 -*-
import discord
from discord import app_commands
from discord.ext import commands
import os
import json
import csv
import base64
import requests
import asyncio
from datetime import datetime
from trocr_ocr import trocr_ocr  # ملف TrOCR المنفصل

TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "alvetoteam/DaB-Alliance"
GITHUB_BRANCH = "main"

DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images'
os.makedirs(IMAGE_FOLDER, exist_ok=True)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree
pending_images = {}  # user_id => list of image paths

# --- GitHub Upload ---
def get_file_sha(github_path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get('sha')
    return None

def upload_to_github(file_path, github_path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()
    sha = get_file_sha(github_path)
    data = {
        "message": f"Upload {github_path}",
        "content": content,
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    r = requests.put(url, headers=headers, json=data)
    return r.status_code in [200, 201]

def load_all_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

@bot.event
async def on_ready():
    print(f'✅ Bot is ready as {bot.user}')
    try:
        synced = await tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

@tree.command(name="dab", description="OCR scan command using TrOCR")
@app_commands.describe(action="Type 'run' to start scanning multiple images")
async def dab(interaction: discord.Interaction, action: str):
    if action.lower() == "run":
        pending_images[interaction.user.id] = []
        await interaction.response.send_message("📥 Upload one or more images.\nWhen you're ready, send `done`.")

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    user_id = message.author.id

    if message.author.bot:
        return

    # استقبال الصور
    if message.attachments and user_id in pending_images:
        await message.channel.send("📸 Image received.")
        for image in message.attachments:
            filename = os.path.join(IMAGE_FOLDER, f"{datetime.now().timestamp()}_{image.filename}")
            await image.save(filename)
            pending_images[user_id].append(filename)

    # تنفيذ التحليل عند كتابة "done"
    if message.content.lower() == "done" and user_id in pending_images:
        image_paths = pending_images.pop(user_id)
        if not image_paths:
            await message.channel.send("⚠️ No images were uploaded.")
            return

        await message.channel.send(f"🔍 Analyzing `{len(image_paths)}` image(s)...")
        loop = asyncio.get_running_loop()
        all_texts = []

        for path in image_paths:
            try:
                text = await loop.run_in_executor(None, trocr_ocr, path)
                all_texts.append(text)
            except Exception as e:
                all_texts.append(f"❌ Error reading {os.path.basename(path)}: {e}")

        # معالجة النصوص المجمعة
        full_text = "\n".join(all_texts)
        lines = full_text.strip().split('\n')
        players = []
        temp_power = None
        temp_level = None

        for line in lines:
            line = line.strip()
            if "M" in line:
                try:
                    temp_power = float(line.split("M")[0].split()[-1])
                except:
                    temp_power = None
            elif "Lv." in line:
                try:
                    temp_level = int(line.split("Lv.")[-1].strip().split()[0])
                except:
                    temp_level = None
            else:
                name = line.upper()
                if name and (len(players) == 0 or name != players[-1]['name']):
                    players.append({
                        "name": name,
                        "power": temp_power if temp_power is not None else "Unknown",
                        "level": temp_level if temp_level is not None else "Unknown"
                    })
                    temp_power = None
                    temp_level = None

        names_list = [p['name'] for p in players]
        powers_list = [p['power'] for p in players]
        levels_list = [p['level'] for p in players]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        all_data = load_all_data()
        all_data[timestamp] = {
            "players": names_list,
            "powers": powers_list,
            "levels": levels_list
        }
        save_all_data(all_data)

        csv_filename = f"analysis_{timestamp.replace(':','-').replace(' ', '_')}.csv"
        csv_path = os.path.join(IMAGE_FOLDER, csv_filename)
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Player', 'Power (M)', 'Village Level'])
            for i in range(len(players)):
                writer.writerow([
                    players[i]['name'],
                    players[i]['power'],
                    players[i]['level']
                ])

        for path in image_paths:
            upload_to_github(path, f"upload/{os.path.basename(path)}")
        upload_to_github(DATA_FILE, "upload/data.json")
        upload_to_github(csv_path, f"upload/{csv_filename}")

        await message.channel.send(
            f"📊 Done! Found `{len(players)}` players.\n"
            f"📁 Images uploaded to GitHub.\n"
            f"📎 {csv_filename} attached.",
            file=discord.File(csv_path)
        )

bot.run(TOKEN)
