from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import openai
import requests
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os

app = FastAPI()

VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key("1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE").sheet1

@app.get("/")
def root():
    return {"message": "WhatsApp CRM Bot is working ✅"}

@app.get("/webhook")
def verify_token(request: Request):
    params = request.query_params
    if params.get("hub.verify_token") == VERIFY_TOKEN:
        return int(params.get("hub.challenge"))
    return "Invalid verification token"

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("📩 Webhook получен:", data)

    if data.get("object") == "whatsapp_business_account":
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value")
                messages = value.get("messages")
                if messages:
                    for message in messages:
                        wa_id = message["from"]
                        msg_type = message["type"]
                        user_name = value.get("contacts")[0].get("profile").get("name")
                        timestamp = message.get("timestamp")

                        if msg_type == "text":
                            text = message["text"]["body"]
                            await process_message(wa_id, user_name, text, timestamp)

                        elif msg_type == "audio":
                            media_id = message["audio"]["id"]
                            audio_url = get_audio_url(media_id)
                            audio_text = transcribe_audio(audio_url)
                            if audio_text:
                                await process_message(wa_id, user_name, audio_text, timestamp)
                            else:
                                send_message(wa_id, "Пожалуйста, напишите текстом, чтобы мы точно поняли ваш запрос.")

    return JSONResponse(status_code=200, content={"message": "EVENT_RECEIVED"})

def get_audio_url(media_id):
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    response = requests.get(url, headers=headers)
    return response.json().get("url")

def transcribe_audio(audio_url):
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    audio_data = requests.get(audio_url, headers=headers).content
    response = openai.audio.transcriptions.create(model="whisper-1", file=audio_data, response_format="text", language="ru")
    return response

async def process_message(wa_id, user_name, message, timestamp):
    translated = translate_text(message, target_lang="ur")

    sheet.append_row([str(datetime.now()), user_name, wa_id, message, translated])

    # Ответ клиенту от ChatGPT
    reply = get_chatgpt_reply(message)
    send_message(wa_id, reply)

    # Переводим ответ и отправляем сотруднику
    reply_ur = translate_text(reply, target_lang="ur")
    forward_to_staff(reply_ur)

def send_message(phone_number, message):
    url = f"https://graph.facebook.com/v19.0/647813198421368/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Ответ отправлен:", response.status_code, response.text)

def get_chatgpt_reply(prompt):
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

def translate_text(text, target_lang="ur"):
    completion = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"Переведи на {target_lang}. Только перевод."},
            {"role": "user", "content": text}
        ]
    )
    return completion.choices[0].message.content.strip()

def forward_to_staff(message):
    # Здесь можно заменить на номер сотрудника и повторно вызвать send_message
    staff_number = "971501234567"  # пример
    send_message(staff_number, message)
