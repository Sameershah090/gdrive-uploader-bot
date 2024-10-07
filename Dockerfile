FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY telegram_gdrive_downloader.py .

# Create a volume for persistent storage of token.pickle
VOLUME /app/data/token.pickle

CMD ["python", "telegram_gdrive_downloader.py"]
