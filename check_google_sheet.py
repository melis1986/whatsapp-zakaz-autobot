from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, HTMLResponse
import traceback
import requests
import gspread
from google.oauth2.service_account import Credentials
import os
from openai import OpenAI
from datetime import datetime
import subprocess

app = FastAPI()

# === CONFIG ===
VERIFY_TOKEN = "autoland777"
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"
SPREADSHEET_KEY = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PHONE_NUMBER_ID = "647813198421368"

CLIENT_NUMBER = "971501109728"
EMPLOYEE_NUMBER = "996703731000"

last_debug_info = {}

# === ROOT TEST ===
@app.get("/")
def read_root():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
        headers = sheet.row_values(1)
        return HTMLResponse(content=f"""
        <html><head><title>CRM Бот</title></head><body>
        <h1>✅ Бот подключён</h1>
        <ul>{''.join([f'<li>{header}</li>' for header in headers])}</ul>
        </body></html>
        """)
    except Exception as e:
        return JSONResponse(content={"error": str(e), "trace": traceback.format_exc()}, status_code=500)

# === VERIFY WEBHOOK ===
@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=params.get("hub.challenge"), status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)

# === GPT
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
        print("GPT Error:", e)
        return "Произошла ошибка при обращении к ChatGPT."

# === DETECT LANGUAGE
def detect_language(text):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        lang = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Определи язык этого текста: только 'кыргызский' или 'русский'."},
                {"role": "user", "content": text}
            ]
        ).choices[0].message.content.lower()
        return "кыргызский" if "кыргыз" in lang else "русский"
    except Exception as e:
        print("Lang Detect Error:", e)
        return "русский"

# === TRANSLATE
def translate_to_english(text):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        return client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a translator. Translate to simple English."},
                {"role": "user", "content": text}
            ]
        ).choices[0].message.content.strip()
    except Exception as e:
        print("Translate Error:", e)
        return "[Translation Error]"

# === BACK TRANSLATION
def translate_back(text, lang):
    if lang == "русский":
        return text
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        return client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Переведи на {lang} язык."},
                {"role": "user", "content": text}
            ]
        ).choices[0].message.content.strip()
    except Exception as e:
        print("Back Translate Error:", e)
        return text

# === TRANSCRIBE AUDIO
def transcribe_audio(file_path):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        with open(file_path, "rb") as f:
            return client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text"
            )
    except Exception as e:
        print("Transcribe Error:", e)
        return "[Ошибка расшифровки]"

# === SAVE TO SHEET
def save_to_sheet(from_number, lang, original, eng, gpt, final):
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ])
        gc = gspread.authorize(creds)
        sheet = gc.open_by_key(SPREADSHEET_KEY).sheet1
        sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", from_number, lang, original, eng, gpt, final, "Новый"
        ], value_input_option="USER_ENTERED")
    except Exception as e:
        print("Sheet Save Error:", e)

# === WHATSAPP REPLY
def send_whatsapp_reply(number: str, message: str):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": number,
        "type": "text",
        "text": {"body": message}
    }
    r = requests.post(url, json=payload, headers=headers)
    print("📤", number, r.status_code, r.text)

# === WEBHOOK PROCESSING
@app.post("/webhook")
async def receive_webhook(request: Request):
    global last_debug_info
    try:
        data = await request.json()
        msg = data["entry"][0]["changes"][0]["value"]["messages"][0]
        from_number = msg["from"]
        msg_type = msg["type"]

        if from_number == CLIENT_NUMBER:
            if msg_type == "text":
                text = msg["text"]["body"]
                lang = detect_language(text)
                eng = translate_to_english(text)
                gpt = ask_chatgpt(eng)
                final = translate_back(gpt, lang)

                send_whatsapp_reply(CLIENT_NUMBER, final)
                send_whatsapp_reply(EMPLOYEE_NUMBER, eng)
                save_to_sheet(from_number, lang, text, eng, gpt, final)
                last_debug_info = {"from": from_number, "text": text, "lang": lang, "eng": eng, "gpt": gpt, "final": final}

            elif msg_type == "audio":
                audio_id = msg["audio"]["id"]
                media_url = f"https://graph.facebook.com/v18.0/{audio_id}"
                headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
                audio_info = requests.get(media_url, headers=headers).json()
                file_url = audio_info.get("url")

                audio_bin = requests.get(file_url, headers=headers).content
                with open("/tmp/audio.ogg", "wb") as f: f.write(audio_bin)
                subprocess.run(["ffmpeg", "-y", "-i", "/tmp/audio.ogg", "/tmp/audio.wav"], check=True)

                transcript = transcribe_audio("/tmp/audio.wav")
                lang = detect_language(transcript)
                eng = translate_to_english(transcript)
                gpt = ask_chatgpt(eng)
                final = translate_back(gpt, lang)

                send_whatsapp_reply(CLIENT_NUMBER, final)
                send_whatsapp_reply(EMPLOYEE_NUMBER, eng)
                save_to_sheet(from_number, lang, transcript, eng, gpt, final)
                last_debug_info = {"from": from_number, "audio": transcript, "lang": lang, "eng": eng, "gpt": gpt, "final": final}

        elif from_number == EMPLOYEE_NUMBER and msg_type == "text":
            send_whatsapp_reply(CLIENT_NUMBER, msg["text"]["body"])

    except Exception as e:
        print("❌ Ошибка:", e)
        traceback.print_exc()

# === DEBUG INFO
@app.get("/debug")
def get_debug():
    return JSONResponse(content=last_debug_info if last_debug_info else {"message": "Нет данных"})
