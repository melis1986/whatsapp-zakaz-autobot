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
        headers = sheet.row_values(1)

        return HTMLResponse(content=f"""
        <html>
        <head>
            <title>CRM Бот Автозапчасти</title>
            <style>
                body {{ font-family: Arial, sans-serif; background: #f4f4f4; padding: 20px; }}
                h1 {{ color: #2c3e50; }}
                ul {{ list-style-type: none; padding: 0; }}
                li {{
                    background: #ecf0f1;
                    margin: 5px 0;
                    padding: 10px;
                    border-left: 6px solid #27ae60;
                    font-size: 16px;
                }}
            </style>
        </head>
        <body>
            <h1>✅ Бот подключён к Google Sheets</h1>
            <h2>Заголовки таблицы работают:</h2>
            <ul>
                {''.join([f'<li>✔️ {header}</li>' for header in headers])}
            </ul>
        </body>
        </html>
        """, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"error": "Ошибка подключения", "details": str(e), "trace": traceback.format_exc()},
            status_code=500
        )

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=params.get("hub.challenge"), status_code=200)
    return PlainTextResponse(content="Verification failed", status_code=403)

def ask_chatgpt(question):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты помощник по автозапчастям. Отвечай коротко и по делу."},
                {"role": "user", "content": question}
            ]
        )
        return res.choices[0].message.content.strip()
    except: return "[Ошибка ChatGPT]"

def detect_language(text):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Определи язык этого текста: только 'кыргызский' или 'русский'."},
                {"role": "user", "content": text}
            ]
        )
        lang = res.choices[0].message.content.strip().lower()
        return "кыргызский" if "кыргыз" in lang else "русский"
    except: return "русский"

def translate_to_english(text):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Translate the following text from Russian or Kyrgyz into English."},
                {"role": "user", "content": text}
            ]
        )
        return res.choices[0].message.content.strip()
    except: return "[Translation Error]"

def translate_back(text, lang):
    if lang == "русский": return text
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Переведи на {lang} язык."},
                {"role": "user", "content": text}
            ]
        )
        return res.choices[0].message.content.strip()
    except: return text

def transcribe_audio(file_path):
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        with open(file_path, "rb") as f:
            return client.audio.transcriptions.create(
                model="whisper-1", file=f, response_format="text"
            )
    except: return "[Ошибка расшифровки аудио]"

def save_to_sheet(from_number, lang, orig, eng, gpt, back):
    try:
        creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        sheet = gspread.authorize(creds).open_by_key(SPREADSHEET_KEY).sheet1
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, "", from_number, lang, orig, eng, gpt, back, "Новый"], value_input_option="USER_ENTERED")
    except Exception as e:
        print("❌ Ошибка сохранения в таблицу:", e)

def send_whatsapp_reply(number, msg):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": number, "type": "text", "text": {"body": msg}}
    return requests.post(url, json=data, headers=headers).status_code

@app.post("/webhook")
@app.post("/webhook")
async def receive_webhook(request: Request):
    global last_debug_info
    data = await request.json()
    try:
        messages = data["entry"][0]["changes"][0]["value"].get("messages", [])
        if not messages:
            return JSONResponse(content={"info": "No message to process"}, status_code=200)
        msg = messages[0]
        from_number = msg["from"]
        msg_type = msg["type"]

        if msg_type == "text":
            text = msg["text"]["body"]
            if from_number == CLIENT_NUMBER:
                lang = detect_language(text)
                to_emp = translate_to_english(text)
                reply_en = ask_chatgpt(to_emp)
                back = translate_back(reply_en, lang)

                send_whatsapp_reply(CLIENT_NUMBER, back)
                send_whatsapp_reply(EMPLOYEE_NUMBER, to_emp)

                save_to_sheet(from_number, lang, text, to_emp, reply_en, back)

            elif from_number == EMPLOYEE_NUMBER:
                send_whatsapp_reply(CLIENT_NUMBER, text)

        elif msg_type == "audio" and from_number == CLIENT_NUMBER:
            voice_id = msg["audio"]["id"]
            media_url = requests.get(f"https://graph.facebook.com/v18.0/{voice_id}", headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}).json().get("url")
            audio_content = requests.get(media_url, headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}"}).content
            with open("/tmp/audio.ogg", "wb") as f: f.write(audio_content)
            subprocess.run(["ffmpeg", "-y", "-i", "/tmp/audio.ogg", "/tmp/audio.wav"])
            transcript = transcribe_audio("/tmp/audio.wav")
            lang = detect_language(transcript)
            to_emp = translate_to_english(transcript)
            reply_en = ask_chatgpt(to_emp)
            back = translate_back(reply_en, lang)
            send_whatsapp_reply(CLIENT_NUMBER, back)
            send_whatsapp_reply(EMPLOYEE_NUMBER, to_emp)
            save_to_sheet(from_number, lang, transcript, to_emp, reply_en, back)
    except Exception as e:
        print("❌ Ошибка обработки запроса:", e)
        traceback.print_exc()
@app.get("/debug")
def get_debug_info():
    return JSONResponse(content=last_debug_info or {"message": "Нет данных"})
