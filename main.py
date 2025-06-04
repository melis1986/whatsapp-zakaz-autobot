from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def read_root():
    try:
        # Подключение через сервисный JSON-файл
        creds = Credentials.from_service_account_file(
            "/etc/secrets/service_account.json",
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        gc = gspread.authorize(creds)

        # Название таблицы (убедись, что совпадает!)
        spreadsheet = gc.open("CRM Autoparts")

        # Подключение к первому листу
        worksheet = spreadsheet.worksheet("Лист1")

        # Чтение первой строки таблицы
        first_row = worksheet.row_values(1)

        return {
            "message": "Успешное подключение ✅",
            "first_row": first_row
        }

    except Exception as e:
        return JSONResponse(content={"error": f"Ошибка подключения: {str(e)}"}, status_code=500)
