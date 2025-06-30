FROM python:3.10-slim

# Set working dir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy your bot code
COPY . .

CMD ["python", "bot.py"]
