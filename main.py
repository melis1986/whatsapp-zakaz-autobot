from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import traceback
import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import re
from openai import OpenAI

app = FastAPI()

# === CONFIG ===
VERIFY_TOKEN = "autoland777"
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"
SPREADSHEET_KEY = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PHONE_NUMBER_ID = "647813198421368"
EMPLOYEE_NUMBER = "971501109728"

# === ROOT TEST ===
@app.get("/")
def read_root():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
        first_row = sheet.row_values(1)

        return JSONResponse(content={
            "message": "Бот успешно подключён к Google Sheets ✅",
            "headers": first_row
        })
    except Exception as e:
        return JSONResponse(
            content={
                "error": "Ошибка подключения",
                "details": str(e),
                "trace": traceback.format_exc()
            },
            status_code=500
        )

# === WEBHOOK VERIFY ===
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200, media_type="text/plain")
    return PlainTextResponse(content="Verification failed", status_code=403, media_type="text/plain")

# === GPT RESPONSE ===
def ask_chatgpt(question):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помощник по автозапчастям. Отвечай кратко и по делу."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Ошибка GPT:", e)
        return "Произошла ошибка при обращении к ChatGPT."

# === DETECT LANGUAGE ===
def detect_language(text):
    if re.search(r'[үңөӱһҥҗө]', text.lower()):
        return "kyrgyz"
    elif re.search(r'[а-яА-ЯёЁ]', text):
        return "russian"
    else:
        return "russian"

# === TRANSLATE ===
def translate(text, source_lang, target_lang):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = f"Translate this from {source_lang} to {target_lang}:\n\n{text}"
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ Ошибка перевода:", e)
        return "[Translation Error]"

# === SEND WHATSAPP ===
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
    return response.status_code

# === WEBHOOK MAIN ===
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📩 Webhook получен:", data)

    try:
        entry = data["entry"][0]
        change = entry["changes"][0]["value"]
        messages = change.get("messages")

        if messages:
            msg = messages[0]
            from_number = msg["from"]
            text = msg["text"]["body"]
            print("📨 Получено сообщение:", text)

            # Определяем язык клиента
            client_lang = detect_language(text)

            # Переводим на английский для сотрудника
            to_employee = translate(text, client_lang, "english")
            send_whatsapp_reply(EMPLOYEE_NUMBER, to_employee)

            # Получаем ответ от ChatGPT как сотрудник
            response_en = ask_chatgpt(to_employee)

            # Переводим обратно клиенту
            reply_to_client = translate(response_en, "english", client_lang)
            send_whatsapp_reply(from_number, reply_to_client)

    except Exception as e:
        print("❌ Ошибка обработки:", e)
        traceback.print_exc()
