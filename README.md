# Kingshot Discord OCR Bot

A simple Python-based Discord bot that uses OCR (Tesseract) to extract player data (name, village, power) from game screenshots sent in the chat using the `!تحليل` command. Perfect for tracking progress in games like Kingshot.

## Features
- Supports image uploads via `!تحليل`
- Uses Tesseract OCR to extract text
- Sends clean results back to the channel

## Local Setup
1. Install Python 3.11+
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Install Tesseract OCR:
- Windows: https://github.com/tesseract-ocr/tesseract/wiki
- Mac/Linux: https://tesseract-ocr.github.io/

4. Set your Discord bot token as an environment variable:
```
export DISCORD_BOT_TOKEN=your_token_here
```

5. Run the bot:
```
python bot.py
```

## Deploy to Railway
- Push this project to GitHub
- Create a new Railway project → link GitHub
- Add environment variable `DISCORD_BOT_TOKEN`
- Deploy and you're done 🎉