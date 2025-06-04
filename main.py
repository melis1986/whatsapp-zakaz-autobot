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
