import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from telegram import Bot
import aiohttp
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/download/{chat_id}/{message_id}")
async def download_file(chat_id: int, message_id: int):
    try:
        message = await bot.get_message(chat_id=chat_id, message_id=message_id)
        if not message.document and not message.video and not message.audio and not message.voice:
            raise HTTPException(status_code=404, detail="No file found in this message")

        file = await bot.get_file(message.document.file_id if message.document else 
                                  message.video.file_id if message.video else 
                                  message.audio.file_id if message.audio else 
                                  message.voice.file_id)
        file_url = file.file_path

        async def file_stream():
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.telegram.org/file/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/{file_url}") as resp:
                    while True:
                        chunk = await resp.content.read(8192)
                        if not chunk:
                            break
                        yield chunk

        headers = {
            'Content-Disposition': f'attachment; filename="{message.document.file_name if message.document else "file"}"',
            'Content-Type': message.document.mime_type if message.document else 'application/octet-stream'
        }
        return StreamingResponse(file_stream(), headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream/{chat_id}/{message_id}", response_class=HTMLResponse)
async def stream_file(request: Request, chat_id: int, message_id: int):
    try:
        message = await bot.get_message(chat_id=chat_id, message_id=message_id)
        if not message.document and not message.video and not message.audio and not message.voice:
            raise HTTPException(status_code=404, detail="No file found in this message")

        file_type = "document" if message.document else "video" if message.video else "audio" if message.audio else "voice"
        file_name = message.document.file_name if message.document else "video" if message.video else "audio" if message.audio else "voice"
        
        return templates.TemplateResponse("stream.html", {
            "request": request,
            "chat_id": chat_id,
            "message_id": message_id,
            "file_type": file_type,
            "file_name": file_name
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
