from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
from fastapi.responses import JSONResponse
import traceback

app = FastAPI()

@app.get("/")
def read_root():
    try:
        SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"

        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        gc = gspread.authorize(creds)

        spreadsheet = gc.open_by_key("1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE")
        sheet = spreadsheet.sheet1
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
from fastapi.responses import PlainTextResponse  # обязательно импортировать

VERIFY_TOKEN = "autoland777"  # должен совпадать с тем, что ввёл в Meta

@app.get("/webhook")
async def verify_webhook(request: Request):
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        return PlainTextResponse(content="Verification failed", status_code=403)

@app.post("/webhook")
async def receive_webhook(request: Request):
    data = await request.json()
    print("📩 Входящее сообщение:", data)
    return {"status": "received"}
