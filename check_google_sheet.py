import gspread
from google.oauth2.service_account import Credentials

# Путь к JSON-файлу (если он на рабочем столе)
SERVICE_ACCOUNT_FILE = '/Users/melisaldaiar/Desktop/whatsapp-order-bot-461808-5acddb53bf52.json'

# Указываем права доступа
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=scopes
)

# Новый ID таблицы (проверь внимательно регистр букв!)
spreadsheet_id = '1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE'

# Подключаемся и читаем первую строку
client = gspread.authorize(credentials)
sheet = client.open_by_key(spreadsheet_id).worksheet("Лист1")

print(sheet.row_values(1))
