from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import traceback
import requests
import os
import gspread
import tempfile
from openai import OpenAI
from google.oauth2.service_account import Credentials

app = FastAPI()

# === CONFIG ===
VERIFY_TOKEN = "autoland777"
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"
SPREADSHEET_KEY = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = "647813198421368"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# === ROOT TEST ===
@app.get("/")
def root():
    return {"message": "WhatsApp CRM Bot is working ✅"}

# === VERIFY WEBHOOK ===
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)

# === SEND MESSAGE ===
def send_whatsapp_reply(recipient_number: str, message: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, json=payload, headers=headers)
    print("📤 Ответ отправлен:", response.status_code, response.text)

# === TRANSCRIBE AUDIO ===
def transcribe_audio(file_url: str) -> str:
    audio = requests.get(file_url, headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}).content
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
        tmp.write(audio)
        tmp_path = tmp.name
    with open(tmp_path, "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
            response_format="text",
            language="ru"
        )
    return transcript

# === TRANSLATE ===
def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    messages = [
        {"role": "system", "content": f"Переведи с {source_lang} на {target_lang}. Только перевод."},
        {"role": "user", "content": text}
    ]
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    return result.choices[0].message.content.strip()

# === GOOGLE SHEETS LOG ===
def log_to_sheet(number, original, translated):
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
    sheet.append_row([number, original, translated])

# === WEBHOOK HANDLER ===
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📩 Webhook получен:", data)
    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages")
        if not messages:
            return {"status": "no_messages"}

        msg = messages[0]
        from_number = msg["from"]
        msg_type = msg["type"]

        if msg_type == "audio":
            media_id = msg["audio"]["id"]
            media_url_req = requests.get(
                f"https://graph.facebook.com/v18.0/{media_id}",
                headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
            )
            media_url = media_url_req.json()["url"]
            transcript = transcribe_audio(media_url)

            # Ответ клиенту, чтобы он всегда писал текст
            send_whatsapp_reply(from_number, "🎙️ Вы отправили голосовое сообщение. Пожалуйста, напишите, чтобы мы точно поняли вашу заявку.")

            urdu = translate_text(transcript, "русского", "урду")
            reply_urdu = translate_text("Понял, сейчас уточним деталь у поставщика.", "русского", "урду")
            reply_ru = translate_text(reply_urdu, "урду", "русский")

            send_whatsapp_reply(from_number, reply_ru)
            log_to_sheet(from_number, transcript, urdu)
            return {"status": "audio_processed"}

        elif msg_type == "text":
            text = msg["text"]["body"]
            urdu = translate_text(text, "русского", "урду")
            reply_urdu = translate_text("Понял, сейчас уточним деталь у поставщика.", "русского", "урду")
            reply_ru = translate_text(reply_urdu, "урду", "русский")

            send_whatsapp_reply(from_number, reply_ru)
            log_to_sheet(from_number, text, urdu)
            return {"status": "text_processed"}

        else:
            send_whatsapp_reply(from_number, "Пожалуйста, отправьте текст или голосовое сообщение.")
            return {"status": "unsupported"}

    except Exception as e:
        print("❌ Ошибка:", e)
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
