# ezy.py

# ezy.py

# ezy.py
import os, json, csv, base64, requests
import easyocr
from datetime import datetime

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

    data = {
        "message": f"Upload {github_path}",
        "content": content,
        "branch": GITHUB_BRANCH
    }

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    r = requests.put(url, headers=headers, json=data)
    print(f"📤 Upload {github_path}: {r.status_code}")
    return r.status_code in [200, 201]

def analyze_image(filename):
    reader = easyocr.Reader(['en'], gpu=False)
    results = reader.readtext(filename, detail=0)

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
    filename = f"analysis_{timestamp.replace(':','-').replace(' ', '_')}.csv"
    path = os.path.join(IMAGE_FOLDER, filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Player', 'Power (M)', 'Village Level'])
        for i in range(max(len(players), len(powers), len(levels))):
            writer.writerow([
                players[i] if i < len(players) else "Unknown",
                powers[i] if i < len(powers) else "Unknown",
                levels[i] if i < len(levels) else "Unknown"
            ])
    return path, filename
