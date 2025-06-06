from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import traceback
import requests
from google.oauth2.service_account import Credentials
import os
from openai import OpenAI

app = FastAPI()

# === CONFIG ===
VERIFY_TOKEN = "autoland777"
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"
SPREADSHEET_KEY = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = "647813198421368"

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

# === CHATGPT FUNCTION ===
def ask_chatgpt(prompt):
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise Exception("OPENAI_API_KEY не установлен в переменных окружения")

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помогаешь с автозапчастями. Отвечай кратко и по делу."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ Ошибка при обращении к ChatGPT: {e}")
        return "Извините, произошла ошибка при подключении к ИИ."

# === WHATSAPP SEND ===
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

# === WEBHOOK POST ===
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
            msg_type = msg["type"]

            if msg_type == "audio":
                reply = "🎙️ Вы отправили голосовое сообщение. Пожалуйста, напишите текстом, чтобы мы точно поняли вашу заявку."
                send_whatsapp_reply(from_number, reply)
                return {"status": "audio_handled"}

            elif msg_type == "text":
                text = msg["text"]["body"]
                print("📨 Получено сообщение:", text)
                reply = ask_chatgpt(text)
                send_whatsapp_reply(from_number, reply)
                return {"status": "text_handled"}

            else:
                send_whatsapp_reply(from_number, "Извините, поддерживаются только текстовые и голосовые сообщения.")
                return {"status": "unsupported_message"}

    except Exception as e:
        print("❌ Ошибка обработки запроса:", e)
        traceback.print_exc()

# === OPENAI TEST ===
@app.get("/test-openai")
def test_openai_key():
    try:
        from openai import OpenAI
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"status": "error", "message": "❌ OPENAI_API_KEY не установлен в окружении"}

        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Проверка ключа OpenAI. Ты меня слышишь?"}
            ],
            temperature=0.5
        )
        return {
            "status": "success",
            "reply": response.choices[0].message.content.strip()
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
