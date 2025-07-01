#test


import os
import base64
import requests

# إعدادات GitHub
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = "alvetoteam/Dab-alliance"  # بدون مسافات
GITHUB_BRANCH = "main"
GITHUB_PATH = "uploads/test/test_upload.txt"

def upload_test_file():
    content = base64.b64encode(b"This is a test file from test_github.py").decode()
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "message": "Test upload from test_github.py",
        "content": content,
        "branch": GITHUB_BRANCH
    }

    response = requests.put(url, headers=headers, json=data)

    print(f"🧪 Test Upload Status: {response.status_code}")
    if response.status_code in [200, 201]:
        print("✅ Upload successful! Check your GitHub repo.")
    else:
        print("❌ Upload failed.")
        print("Response:", response.text)

if __name__ == "__main__":
    upload_test_file()
