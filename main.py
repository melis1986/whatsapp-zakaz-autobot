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
        
        # Пробуем прочитать первую строку
        sheet = spreadsheet.sheet1
        values = sheet.row_values(1)
        
        return {"message": "✅ Бот подключён. Первая строка таблицы:", "row_1": values}
    
    except Exception as e:
        return JSONResponse(content={"error": f"Ошибка подключения: {str(e)}"}, status_code=500)
