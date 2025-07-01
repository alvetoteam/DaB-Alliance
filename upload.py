# upload.py
import base64
import os
import requests

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "alvetoteam/DaB-Alliance"
GITHUB_BRANCH = "main"

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

    response = requests.put(url, headers=headers, json=data)
    print(f"📤 Upload {github_path}: {response.status_code}")
    return response.status_code in [200, 201]
