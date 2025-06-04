from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def read_root():
    try:
        creds = Credentials.from_service_account_file(
            "/etc/secrets/service_account.json",
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        gc = gspread.authorize(creds)

        # Подключаем таблицу по названию
        spreadsheet = gc.open("1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE")

        return {"message": "✅ Бот подключен к таблице успешно!"}

    except Exception as e:
        return JSONResponse(content={"error": f"Ошибка подключения: {str(e)}"}, status_code=500)
