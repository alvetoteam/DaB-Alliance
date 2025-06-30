import discord
import pytesseract
from PIL import Image
import io
import os
import json
import time
from datetime import datetime

# — Configuration —
TOKEN     = os.getenv('DISCORD_BOT_TOKEN')
DATA_FILE = 'data.json'

# — Discord client setup —
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# — Load & save plaintext JSON with timestamp —
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        return json.load(f).get('players', {})

def save_data(players):
    with open(DATA_FILE, 'w') as f:
        json.dump({'players': players}, f, indent=2)

# — Bot startup event —
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    await client.change_presence(activity=discord.Game(name="Type 'dab help' for commands"))

user_waiting = set()

@client.event
async def on_message(message):
    if message.author.bot:
        return

    uid = message.author.id
    cmd = message.content.lower().strip()

    # — Help: dab help —
    if cmd == 'dab help':
        embed = discord.Embed(
            title="🛠️ DaB Alliance OCR Bot – Help",
            description="All available commands:",
            color=discord.Color.purple()
        )
        embed.add_field("• `dab`", "Begin OCR flow: will prompt you to upload an image.", inline=False)
        embed.add_field("• `sdab`", "Show stored data (power, level & last update) in a table.", inline=False)
        embed.add_field("• `xdab`", "Shut down the bot gracefully.", inline=False)
        embed.set_footer(text="Powered by KSA – DaB alliance (vlaibee)")
        await message.channel.send(embed=embed)
        return

    # — sdab: display all stored data with last_updated —
    if cmd == 'sdab':
        players = load_data()
        embed = discord.Embed(
            title="📊 Stored Player Data",
            color=discord.Color.blue()
        )
        if not players:
            embed.description = "No player data found."
        else:
            # build markdown table header
            table  = "| Player     | Power     | Level | Last Updated          |\n"
            table += "|------------|-----------|-------|-----------------------|\n"
            for name, info in players.items():
                p_str = f"{info['power']:,}"
                l_str = str(info['level'])
                t_str = info.get('last_updated', '—')
                table += f"| {name:<10} | {p_str:>9} | {l_str:>5} | {t_str:<21} |\n"
            embed.add_field(name="\u200b", value=table, inline=False)
        embed.set_footer(text="Data provided by KSA – DaB alliance (vlaibee)")
        await message.channel.send(embed=embed)
        return

    # — xdab: shutdown —
    if cmd == 'xdab':
        await message.channel.send("⚙️ Shutting down, bye!")
        await client.close()
        return

    # — dab: start OCR flow —
    if cmd == 'dab':
        if uid not in user_waiting:
            user_waiting.add(uid)
            await message.channel.send(
                "📥 Please upload an image now for analysis.\n"
                "🛠️ *This bot was crafted by KSA – DaB alliance. Stay vigilant.* *(vlaibee)*"
            )
        return

    # — Handle uploaded image after dab —
    if uid in user_waiting and message.attachments:
        user_waiting.remove(uid)
        await message.channel.send("✅ Image received... Analyzing now 🔍")
        start = time.time()

        # OCR extraction
        img_bytes = await message.attachments[0].read()
        image    = Image.open(io.BytesIO(img_bytes))
        text     = pytesseract.image_to_string(image)
        lines    = [l.strip() for l in text.splitlines() if l.strip()]

        # load old data
        old_players = load_data()
        new_players = {}
        rows        = []

        now_str = datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

        for ln in lines:
            parts = ln.split()
            if len(parts) >= 3:
                name  = parts[0].upper()
                try:
                    power = int(parts[1].replace(",", ""))
                    level = int(parts[2])
                except:
                    continue

                old = old_players.get(name, {"power":0, "level":0, "last_updated": "—"})
                dp  = power - old['power']
                dl  = level - old['level']
                if dp > 0 or dl > 0:
                    status = "✅ Improved"
                elif dp == 0 and dl == 0:
                    status = "🔁 Same"
                else:
                    status = "⚠️ Decreased"

                rows.append((name, old['power'], power, dp, old['level'], level, dl, status, now_str))
                new_players[name] = {"power": power, "level": level, "last_updated": now_str}

        # merge & save
        merged = old_players.copy()
        merged.update(new_players)
        save_data(merged)

        elapsed = round(time.time() - start, 2)

        # build result embed
        embed = discord.Embed(
            title="📊 Analysis Results",
            description=f"⏱️ Completed in **{elapsed}s**",
            color=discord.Color.green()
        )
        table = ("`Player     OldP      NewP      ΔP       OldL NewL ΔL   Status   Updated`\n"
                 "`--------------------------------------------------------------------------`\n")
        for r in rows:
            table += (
                f"`{r[0]:<10}{r[1]:<10}{r[2]:<10}{r[3]:<8}{r[4]:<5}"
                f"{r[5]:<5}{r[6]:<5}{r[7]:<9}{r[8]}`\n"
            )
        embed.add_field(name="Details", value=table, inline=False)
        embed.set_footer(text="🧠 Don’t forget to thank KSA… for doing *all the hard work*, obviously 😏")

        await message.channel.send(embed=embed)
        return

# — Startup —
client.run(TOKEN)
