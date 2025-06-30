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

# تأكد من وجود مجلد الصور
os.makedirs('images', exist_ok=True)

def load_previous_players():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return data.get('players', {})
    except FileNotFoundError:
        return {}

def save_players(players):
    with open(DATA_FILE, 'w') as f:
        json.dump({'players': players}, f, indent=2)

@client.event
async def on_ready():
    print(f'✅ Logged in as {client.user}!')

@client.event
async def on_message(message):
    if message.author.bot:
        return

    content = message.content.lower()

    if content == "dab":
        await message.channel.send(
            "📥 Please upload an image now for analysis.\n"
            "Commands:\n"
            "`dab help` - Show help info\n"
            "`dab data` - Show saved players data\n"
            "`xdab` - Stop the bot\n"
        )
        client.analysis_mode = True
        return

    if content == "dab help":
        help_msg = (
            "**DaB Bot Commands:**\n"
            "`dab` - Start image upload and analysis session\n"
            "`dab data` - Show saved player data with timestamps\n"
            "`xdab` - Stop the bot\n\n"
            "_Note: Powered by KSA – DaB alliance (vlaibee)_ 😏"
        )
        await message.channel.send(help_msg)
        return

    if content == "dab data":
        data = load_previous_players()
        if not data:
            await message.channel.send("📂 No player data available.")
        else:
            msg = "**Saved Player Data:**\n"
            for player, info in data.items():
                msg += f"- **{player}** | Power: {info['power']} | Village Level: {info['village_level']} | Last Seen: {info['timestamp']}\n"
            await message.channel.send(msg + "\n📝 _Note: Powered by KSA – DaB alliance (vlaibee)_")
        return

    if content == "xdab":
        await message.channel.send("🛑 Bot is shutting down... Bye! 👋")
        await client.close()
        return

    # استقبال الصور فقط اذا دخلنا في وضع التحليل
    if getattr(client, 'analysis_mode', False) and message.attachments:
        await message.channel.send("✅ Image received... Analyzing now 🔍")

        start_time = time.time()

        attachment = message.attachments[0]
        file_path = f"images/{attachment.filename}"
        await attachment.save(file_path)

        # قراءة الصورة وتشغيل OCR
        image = Image.open(file_path)
        text = pytesseract.image_to_string(image)

        # تنظيف النص
        lines = [line.strip() for line in text.splitlines() if line.strip()]

        # تحميل بيانات اللاعبين القديمة
        old_data = load_previous_players()
        new_data = {}
        duplicates = []

        for line in lines:
            # متوقع شكل السطر: PlayerName power village_level
            # مثال: ALPHA 12345 10
            parts = line.split()
            if len(parts) >= 3:
                player_name = parts[0].upper()
                power = parts[1]
                village_level = parts[2]
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

                if player_name in old_data:
                    duplicates.append(player_name)

                new_data[player_name] = {
                    "power": power,
                    "village_level": village_level,
                    "timestamp": timestamp
                }

        # دمج البيانات الجديدة مع القديمة مع تحديث معلومات اللاعبين الجدد/المحدثين
        merged_data = old_data.copy()
        merged_data.update(new_data)

        save_players(merged_data)

        # بناء رسالة المقارنة - هنا فقط نعطي التنبيه إذا وجدت نفس الأسماء
        comparison_msg = "📄 **OCR Result:**\n```\n" + "\n".join(lines) + "\n```\n"

        if duplicates:
            comparison_msg += f"⚠️ Duplicate players found: {', '.join(duplicates)}\n"

        elapsed = time.time() - start_time
        comparison_msg += f"⏱️ Analysis completed in {elapsed:.2f} seconds.\n"
        comparison_msg += "😏 Don't forget to thank KSA - DaB alliance (vlaibee)"

        await message.channel.send(comparison_msg)

        client.analysis_mode = False

client.run(TOKEN)
