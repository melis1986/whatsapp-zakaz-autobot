import gspread
from google.oauth2.service_account import Credentials

# Путь к JSON-файлу
SERVICE_ACCOUNT_FILE = '/etc/secrets/service_account.json'

# Указываем права доступа
scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=scopes
)

# Новый ID таблицы
spreadsheet_id = "1YHAhKeKzT5in87uf1d5VcT0AnXllhXl4PemviXbPxNE"

# Подключаемся и читаем первую строку
client = gspread.authorize(credentials)
sheet = client.open_by_key(spreadsheet_id).worksheet("Лист1")
print(sheet.row_values(1))
