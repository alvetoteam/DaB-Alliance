import discord
import easyocr
import os
import json
import csv
import base64
import requests
import asyncio
from datetime import datetime

# إعداد المتغيرات
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "alvetoteam/DaB-Alliance"
GITHUB_BRANCH = "main"

DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images'
MODEL_FOLDER = 'models'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

pending_users = set()

# إنشاء مجلدات الملفات
for folder in [IMAGE_FOLDER, MODEL_FOLDER]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# دالة لتحميل نماذج EasyOCR من GitHub الرسمي
def download_easyocr_model(filename):
    url = f"https://github.com/JaidedAI/EasyOCR/raw/master/easyocr/{filename}"
    save_path = os.path.join(MODEL_FOLDER, filename)
    if not os.path.exists(save_path):
        print(f"Downloading {filename} from EasyOCR GitHub...")
        r = requests.get(url)
        if r.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(r.content)
            print(f"{filename} downloaded successfully.")
        else:
            print(f"Failed to download {filename}. Status code: {r.status_code}")
    else:
        print(f"{filename} already exists, skipping download.")

# دوال رفع الملفات إلى GitHub مع دعم التحديث (SHA)
def get_file_sha(github_path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json().get('sha')
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
        data["sha"] = sha  # مهم للتحديث بدل الإضافة الجديدة

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.put(url, headers=headers, json=data)

    if response.status_code in [200, 201]:
        print(f"📤 Upload {github_path}: Success ({response.status_code})")
        return True
    else:
        print(f"❌ Failed to upload {github_path}: {response.status_code}")
        print(f"Response: {response.text}")
        return False

# دوال تحميل وحفظ البيانات محلياً
def load_all_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# دالة OCR تُشغل في Thread منفصل لمنع حظر البوت
def ocr_process(path):
    reader = easyocr.Reader(['en'], gpu=False, model_storage_directory=MODEL_FOLDER)
    return reader.readtext(path, detail=0)

# حدث عند تشغيل البوت
@client.event
async def on_ready():
    print(f'✅ Bot is ready as {client.user}')
    download_easyocr_model("craft_mlt_25k.pth")
    download_easyocr_model("crnn.pth")

# حدث استقبال رسالة
@client.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = message.author.id
    content = message.content.lower()

    if content == 'dab help':
        await message.channel.send(
            "**KSA DaB OCR Bot Help**\n"
            "`dab` - Start scan (then upload image)\n"
            "`sdab` - Show all saved data\n"
            "`xdab` - Shutdown bot"
        )
        return

    if content == 'xdab':
        await message.channel.send("Shutting down... 🛑")
        await client.close()
        return

    if content == 'sdab':
        data = load_all_data()
        if not data:
            await message.channel.send("No data found.")
            return
        reply = "**📂 Saved Player Data:**\n"
        for ts, entry in data.items():
            reply += f"🕒 `{ts}`\n"
            for i in range(len(entry['players'])):
                name = entry['players'][i]
                power = entry['powers'][i] if i < len(entry['powers']) else "?"
                level = entry['levels'][i] if i < len(entry['levels']) else "?"
                reply += f"• `{name}` | `{power}M` | `Lv.{level}`\n"
            reply += "\n"
        await message.channel.send(reply)
        return

    if content == 'dab':
        pending_users.add(user_id)
        await message.channel.send("📥 Please upload an image now.")
        return

    if message.attachments:
        if user_id in pending_users:
            pending_users.remove(user_id)
            await message.channel.send("✅ Image received, analyzing...")

            image = message.attachments[0]
            filename = os.path.join(IMAGE_FOLDER, image.filename)
            await image.save(filename)

            loop = asyncio.get_running_loop()
            try:
                results = await loop.run_in_executor(None, ocr_process, filename)
            except Exception as e:
                await message.channel.send(f"❌ OCR failed: {e}")
                return

            players = []
            temp_power = None
            temp_level = None

            for line in results:
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

            success_image = upload_to_github(filename, f"upload/{os.path.basename(filename)}")
            success_data = upload_to_github(DATA_FILE, "data.json")
            success_csv = upload_to_github(csv_path, csv_filename)

            if success_image:
                image_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/upload/{os.path.basename(filename)}"
            else:
                image_url = "Failed to upload image."

            await message.channel.send(
                f"📊 Done! Found `{len(players)}` players.\n"
                f"🖼️ Image uploaded to GitHub: {image_url}\n"
                f"📎 `{csv_filename}` attached.",
                file=discord.File(csv_path)
            )
        else:
            await message.channel.send("⚠️ Type `dab` first before uploading an image.")

# تشغيل البوت
client.run(TOKEN)
