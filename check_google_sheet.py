def get_sheet_data():
    import gspread
    from google.oauth2.service_account import Credentials
    import json

    creds_path = "/etc/secrets/service_account.json"
    scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
    with open(creds_path) as source:
        creds_dict = json.load(source)

    credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    gc = gspread.authorize(credentials)

    spreadsheet = gc.open_by_key("1YHAhKeKzT5in87uf1d5vCt0AnXllhXl4PemviXbPxNE")
    worksheet = spreadsheet.sheet1
    return worksheet.get_all_records()
