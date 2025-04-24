import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from aiogram import types, Router, F

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
DRIVE_SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'credentials.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=DRIVE_SCOPES
)

service = build('sheets', 'v4', credentials=creds)
drive_service = build('drive', 'v3', credentials=credentials)
spreadsheet_id = os.getenv('SPREADSHEET_ID')
drive_orders_id = os.getenv('DRIVE_ORDERS_ID')


"""Модели для пользователей"""


async def get_user(user_id):
    range_name = 'users!A:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    if not values:
        return None

    for row in values[1:]:
        if len(row) >= 2 and row[0] == str(user_id):
            return row[0]
    return None


async def get_companies():
    range_name = 'companies!A:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    options = []
    for row in values[2:]:
        if len(row) >= 2:
            comp_id = row[0]
            comp_name = row[1]
            options.append((comp_id, comp_name))
    return options


async def get_company_name(comp_id):
    range_name = 'companies!A:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])

    for row in values[2:]:
        if len(row) >= 2 and row[0] == str(comp_id):
            return row[1]

    return None


async def choose_company():
    range_name = 'companies!A:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    logging.info(values)
    buttons = []
    for row in values[2:]:
        if len(row) >= 2:
            comp_id, comp_name = row[0], row[1]
            buttons.append(
                types.InlineKeyboardButton(
                    text=comp_name,
                    callback_data=f"select_company:{comp_id}"
                )
            )

    if not buttons:
        return None
    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard, row_width=1)

    return keyboard


async def get_user_company(user_id):
    range_name = 'users!A:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    if not values:
        return None

    for row in values[2:]:
        if len(row) >= 2 and row[0] == str(user_id):
            return row[1]

    return None


def upload_to_drive(file_path):
    """
    Загружает файл на Google Drive в папку с ID drive_orders_id.
    Возвращает ID загруженного файла или None при ошибке.
    """
    file_name = os.path.basename(file_path)

    metadata = {
        'name': file_name,
        'mimeType': 'text/html',
        'parents': [drive_orders_id]
    }

    media = MediaFileUpload(file_path, mimetype='text/html', resumable=True)

    try:
        resp = drive_service.files().create(
            body=metadata,
            media_body=media,
            fields='id'
        ).execute()
        return resp.get('id')

    except HttpError:
        return None
    except Exception:
        return None


"""Модели для продукт менеджеров"""


async def get_product_manager(user_id):
    range_name = 'users!D:F'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    if not values:
        return None

    for row in values[2:]:
        if len(row) >= 2 and row[0] == str(user_id):
            return row[1]

    return None


async def get_product_manager_password():
    range_name = 'users!N1:P1'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])

    for row in values:
        if row and row[0] == 'Product Manager':
            if len(row) >= 2:
                return row[1]
    raise LookupError("Пароль для Product Manager не найден")


"""Модели для менеджеров"""


async def get_manager(user_id):
    range_name = 'users!G:I'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    if not values:
        return None

    for row in values[2:]:
        if len(row) >= 2 and row[0] == str(user_id):
            return row[1]

    return None


async def get_manager_password():
    range_name = 'users!Q1:S1'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])

    for row in values:
        if row and row[0] == 'Manager':
            if len(row) >= 2:
                return row[1]
    raise LookupError("Пароль для Manager не найден")


"""Модели для контролеров"""


async def get_inspector(user_id):
    range_name = 'users!J:L'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get('values', [])

    if not values:
        return None

    for row in values[2:]:
        if len(row) >= 2 and row[0] == str(user_id):
            return row[1]

    return None


async def get_inspector_password():
    range_name = 'users!T1:V1'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])

    for row in values:
        if row and row[0] == 'Inspector':
            if len(row) >= 2:
                return row[1]
    raise LookupError("Пароль для Inspector не найден")
