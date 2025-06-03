from fastapi import FastAPI
from check_google_sheet import get_sheet_data

app = FastAPI()

@app.get("/")
def read_root():
    try:
        data = get_sheet_data()
        return {"message": "CRM данные успешно получены", "data": data}
    except Exception as e:
        return {"error": str(e)}
