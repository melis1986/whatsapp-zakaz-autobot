import gspread
from google.oauth2.service_account import Credentials

# Путь к JSON-файлу (в Render подмонтирован сюда)
SERVICE_ACCOUNT_FILE = '/etc/secrets/service_account.json'

# OAuth-скоупы
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Авторизация
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

client = gspread.authorize(credentials)

# Укажи ID таблицы, если открываешь по ключу
spreadsheet_id = "1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE"  # Твоя CRM Autoparts
sheet = client.open_by_key(spreadsheet_id).sheet1

# Вывод первой строки таблицы
print("Заголовки таблицы:")
print(sheet.row_values(1))
