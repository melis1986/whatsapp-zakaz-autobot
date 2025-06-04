import gspread
from google.oauth2.service_account import Credentials

# Путь к JSON-файлу на Render
SERVICE_ACCOUNT_FILE = '/etc/secrets/service_account.json'

# Правильные OAuth scopes
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Создаем объект credentials
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

# Авторизация клиента
client = gspread.authorize(credentials)

# ID таблицы (оставь свой)
spreadsheet_id = "1YHAhKeKzT5in87uf1d5VcT0AnXllhXL4PemvixbPxNE"

# Подключение к Google Sheet
sheet = client.open_by_key(spreadsheet_id).worksheet("Лист1")

# Выводим первую строку
print(sheet.row_values(1))
