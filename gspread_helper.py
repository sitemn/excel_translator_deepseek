import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

SHEET_COLUMNS = [
    'Date', 'Product', 'ASIN', 'Model_Requirements',
    'Total_Video', 'Scene', 'Pets_Kids', 'Shooting_Requirements'
]

def setup_gspread_client(credentials_path):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
    return gspread.authorize(creds)

def append_row_to_sheet(gc, spreadsheet_id, worksheet_name, row_data_dict):
    try:
        sh = gc.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet(worksheet_name)
        row_data = [row_data_dict.get(col, "") for col in SHEET_COLUMNS]
        worksheet.append_row(row_data, value_input_option='USER_ENTERED')
        logging.info(f"Appended row to {worksheet_name}: {row_data}")
    except Exception as e:
        logging.error(f"Failed to append to {worksheet_name}: {e}")
