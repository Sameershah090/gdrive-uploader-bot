import os
import pickle
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import requests
from tqdm import tqdm

# Set up your Telegram Bot token
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# Set up Google Drive API credentials
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_credentials():
    creds = None
    if os.path.exists('/app/data/token.pickle'):
        with open('/app/data/token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = Flow.from_client_secrets_file(
                '/app/client_secrets.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open('/app/data/token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

creds = get_credentials()
drive_service = build('drive', 'v3', credentials=creds)

def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, 
                             text="Welcome! Send me links to download files to Google Drive.")

def get_filename_from_cd(cd):
    """
    Get filename from content-disposition
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].strip('"')

def download_and_upload(url):
    """
    Download a file from a given URL and upload to Google Drive
    """
    response = requests.get(url, stream=True, allow_redirects=True)
    
    # Try to get the filename from the Content-Disposition header
    filename = get_filename_from_cd(response.headers.get('Content-Disposition'))
    
    # If filename is not in the header, use a default name
    if not filename:
        filename = 'downloaded_file'
    
    # Get file size for progress
    total_size = int(response.headers.get('content-length', 0))
    
    # Download and upload to Google Drive
    file_metadata = {'name': filename}
    media = io.BytesIO()
    
    for data in tqdm(response.iter_content(chunk_size=1024), 
                     total=total_size//1024, unit='KB', unit_scale=True):
        media.write(data)
    
    media.seek(0)
    file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    file_id = file.get('id')
    download_link = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    return download_link

def handle_message(update, context):
    message = update.message.text
    if message.startswith('http://') or message.startswith('https://'):
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                 text="Downloading and uploading to Google Drive. Please wait...")
        try:
            download_link = download_and_upload(message)
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                     text=f"File uploaded to Google Drive. Download link: {download_link}")
        except Exception as e:
            context.bot.send_message(chat_id=update.effective_chat.id, 
                                     text=f"An error occurred: {str(e)}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, 
                                 text="Please send a valid http or https link.")

def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
