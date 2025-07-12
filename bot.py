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
pending_users = set()

# --- GitHub Upload Utilities ---
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
@app_commands.describe(action="Type 'run' to start scanning")
async def dab(interaction: discord.Interaction, action: str):
    if action.lower() == "run":
        pending_users.add(interaction.user.id)
        await interaction.response.send_message("📥 Please upload an image now.")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.attachments and message.author.id in pending_users:
        pending_users.remove(message.author.id)
        await message.channel.send("✅ Image received, analyzing...")

        image = message.attachments[0]
        filename = os.path.join(IMAGE_FOLDER, image.filename)
        await image.save(filename)

        loop = asyncio.get_running_loop()
        try:
            text = await loop.run_in_executor(None, trocr_ocr, filename)
        except Exception as e:
            await message.channel.send(f"❌ OCR failed: {e}")
            return

        # معالجة النتائج وتخزينها
        lines = text.strip().split('\n')
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

        image_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/upload/{os.path.basename(filename)}" if upload_to_github(filename, f"upload/{os.path.basename(filename)}") else "Failed"
        upload_to_github(DATA_FILE, "upload/data.json")
        upload_to_github(csv_path, f"upload/{csv_filename}")

        await message.channel.send(
            f"📊 Done! Found `{len(players)}` players.\n"
            f"📁 Image uploaded to GitHub: {image_url}\n"
            f"📎 {csv_filename} attached.",
            file=discord.File(csv_path)
        )

bot.run(TOKEN)
