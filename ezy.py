# ezy.py

# ezy.py

import os
import json
import csv
import base64
import requests
from datetime import datetime
import easyocr

DATA_FILE = 'data.json'
IMAGE_FOLDER = 'images'

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GITHUB_REPO = "alvetoteam/Dab alliance"
GITHUB_BRANCH = "main"
GITHUB_FOLDER = "uploads"

if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

def load_all_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_all_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def upload_to_github(file_path, github_path):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{github_path}"
    with open(file_path, "rb") as f:
        content = base64.b64encode(f.read()).decode()

    message = f"Upload {github_path}"
    data = {
        "message": message,
        "content": content,
        "branch": GITHUB_BRANCH
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    r = requests.put(url, headers=headers, json=data)
    print(f"📤 Upload {github_path} status: {r.status_code}")
    return r.status_code in [200, 201]

def analyze_image(filename):
    print("🔍 Initializing EasyOCR reader...")
    reader = easyocr.Reader(['en'], gpu=False)
    print("✅ EasyOCR initialized")
    results = reader.readtext(filename, detail=0)
    print("📋 OCR Results:")
    for r in results:
        print("👉", r)

    players, powers, levels = [], [], []

    for line in results:
        line = line.strip()
        if "M" in line:
            try:
                value = float(line.split("M")[0].split()[-1])
                powers.append(value)
            except:
                continue
        elif "Lv." in line:
            try:
                value = int(line.split("Lv.")[-1].strip().split()[0])
                levels.append(value)
            except:
                continue
        else:
            name = line.upper()
            if name and name not in players:
                players.append(name)

    return players, powers, levels, results

def save_csv(players, powers, levels, timestamp):
    csv_filename = f"analysis_{timestamp.replace(':','-').replace(' ', '_')}.csv"
    csv_path = os.path.join(IMAGE_FOLDER, csv_filename)
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Player', 'Power (M)', 'Village Level'])
        for i in range(max(len(players), len(powers), len(levels))):
            name = players[i] if i < len(players) else "Unknown"
            power = powers[i] if i < len(powers) else "Unknown"
            level = levels[i] if i < len(levels) else "Unknown"
            writer.writerow([name, power, level])
    return csv_path, csv_filename
