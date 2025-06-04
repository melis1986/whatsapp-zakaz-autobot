from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def read_root():
    try:
        # Указываем путь к секретному ключу (он автоматически монтируется Render'ом)
        SERVICE_ACCOUNT_FILE = "/etc/secrets/service_account.json"

        # Правильные OAuth scopes
        SCOPES = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Авторизация через Google API
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        gc = gspread.authorize(creds)

        # Используем ID таблицы (а не имя!)
        spreadsheet_id = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"
        spreadsheet = gc.open_by_key(spreadsheet_id)

        # Читаем первую строку первого листа
        sheet = spreadsheet.sheet1
        first_row = sheet.row_values(1)

        # Возвращаем JSON-ответ
        return JSONResponse(content={
            "message": "Бот подключен к таблице ✅",
            "headers": first_row
        })

    except Exception as e:
    import traceback
    return JSONResponse(
        content={
            "error": "Ошибка подключения",
            "details": str(e),
            "trace": traceback.format_exc()
        },
        status_code=500
    )
