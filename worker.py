# worker.py
import os, requests
from ezy import analyze_image, load_all_data, save_all_data, save_csv, upload_to_github
from datetime import datetime

REPO = "alvetoteam/Dab alliance"
BRANCH = "main"
FOLDER = "images"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def list_github_images():
    url = f"https://api.github.com/repos/{REPO}/contents/{FOLDER}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    files = r.json()
    return [f['name'] for f in files if f['type'] == 'file']

def download_image(filename):
    raw_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{FOLDER}/{filename}"
    r = requests.get(raw_url)
    path = os.path.join("images", filename)
    with open(path, "wb") as f:
        f.write(r.content)
    return path

def main():
    files = list_github_images()
    for fname in files:
        print(f"📥 Processing {fname}")
        local_path = download_image(fname)
        players, powers, levels, _ = analyze_image(local_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        data = load_all_data()
        data[timestamp] = {"players": players, "powers": powers, "levels": levels}
        save_all_data(data)

        csv_path, csv_filename = save_csv(players, powers, levels, timestamp)
        upload_to_github("data.json", "uploads/data.json")
        upload_to_github(csv_path, f"uploads/{csv_filename}")

        print(f"✅ Done {fname}")

if __name__ == "__main__":
    main()
