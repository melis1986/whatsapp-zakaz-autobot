from fastapi import FastAPI
import gspread
from google.oauth2.service_account import Credentials
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
def read_root():
    try:
        # Путь до секрета (файла с ключом)
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("/etc/secrets/service_account.json", scopes=SCOPES)
        gc = gspread.authorize(creds)

        # Пробуем открыть таблицу по названию (замени на своё название!)
        spreadsheet = gc.open_by_key("1YHAhKeKzT5in87uf1d5VcT0AnXllhXl4PemviXbPxNE")
        return {"message": "Бот подключён к таблице ✅"}

    except Exception as e:
        return JSONResponse(content={"error": f"Ошибка подключения: {str(e)}"}, status_code=500)
