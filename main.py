from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import gspread
from google.oauth2.service_account import Credentials
import traceback

app = FastAPI()

# === CONFIG ===
VERIFY_TOKEN = "autoland777"  # Должен совпадать с тем, что в Meta Webhook
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"  # Render автоматически монтирует
SPREADSHEET_KEY = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"  # Google Sheets ID

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

# === WEBHOOK POST ===
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📩 Webhook получен:", data)
    # Здесь можно добавить запись в Google Sheets или обработку
    from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import gspread
from google.oauth2.service_account import Credentials
import traceback

app = FastAPI()

# === CONFIG ===
VERIFY_TOKEN = "autoland777"  # Должен совпадать с тем, что в Meta Webhook
SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"  # Render автоматически монтирует
SPREADSHEET_KEY = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"  # Google Sheets ID

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

# === WEBHOOK POST ===
@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📩 Webhook получен:", data)
    # Здесь можно добавить запись в Google Sheets или обработку
    return {"status": "received"}
