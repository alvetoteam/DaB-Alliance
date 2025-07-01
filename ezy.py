# ezy.py

import json

def analyze_image(image_path):
    # هنا تحط كود تحليل الصورة أو استخراج النص
    print(f"Analyzing image: {image_path}")
    # مثلا ترجع بيانات وهمية
    data = {
        "player_name": "Player1",
        "power": 123456,
        "village_level": 24
    }
    return data

def save_data(data, filename='data.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Data saved to {filename}")

def load_data(filename='data.json'):
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
