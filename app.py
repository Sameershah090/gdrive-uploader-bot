import os
import pickle
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, Dispatcher
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from io import BytesIO

app = Flask(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
PORT = int(os.environ.get('PORT', 5000))

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('Welcome! Send me any file, and I will upload it to your Google Drive.')

def process_file(update: Update, context: CallbackContext) -> None:
    if update.message.document:
        file = update.message.document.get_file()
        file_name = update.message.document.file_name
        file_size = update.message.document.file_size

        update.message.reply_text('Processing your file...')

        file_link = file.get_url()
        response = requests.get(file_link)
        file_content = BytesIO(response.content)

        try:
            creds = None
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    raise Exception("No valid credentials found.")

            service = build('drive', 'v3', credentials=creds)

            file_metadata = {'name': file_name}
            media = MediaIoBaseUpload(file_content, mimetype='application/octet-stream', resumable=True)
            file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            update.message.reply_text(f'File uploaded successfully to Google Drive. File ID: {file.get("id")}')

        except Exception as e:
            update.message.reply_text(f'An error occurred: {str(e)}')

    else:
        update.message.reply_text('Please send a file to upload.')

def setup_webhook(url):
    bot = Bot(TELEGRAM_BOT_TOKEN)
    bot.set_webhook(url + "/webhook")
    return bot

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    dp.process_update(update)
    return 'ok'

if __name__ == '__main__':
    bot = setup_webhook(os.environ.get('APP_URL'))
    dp = Dispatcher(bot, None, workers=0)
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document, process_file))
    app.run(host='0.0.0.0', port=PORT)
