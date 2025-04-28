import os
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import types, Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, InputMediaPhoto, InputMediaAnimation, \
    Message, BufferedInputFile
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from shutil import copyfile
import io
from utils import get_user, get_manager, get_product_manager, get_inspector, spreadsheet_id, service, choose_company, \
    get_product_manager_password, get_manager_password, get_inspector_password, get_user_company, upload_to_drive, \
    get_company_name, get_orders, credentials, generate_application_excel, save_and_send_application, get_order_status, \
    get_manager_companies, get_product_manager_name, get_product_manager_all, get_manager_all, get_inspector_all, \
    get_manager_name, get_inspector_name, upload_report, get_manager_id

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = Router()
message_ids_n = {}


class Form(StatesGroup):
    waiting_for_reg_product_manager = State()
    waiting_for_reg_manager = State()
    waiting_for_reg_inspector = State()
    waiting_for_user_apply_request = State()


@router.callback_query(lambda call: call.data == "close")
async def handle_cancel_selection(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик нажатия на кнопку Закрыть"""
    user_id = callback_query.from_user.id
    if user_id:
        await state.clear()
        await callback_query.message.delete()


@router.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id

    user_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="request")],
            [InlineKeyboardButton(text="📤 Загрузить документ", callback_data="document")],
            [InlineKeyboardButton(text="🔍 Статус заявки", callback_data="status")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

    pm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Список компаний", callback_data="companies")],
            [InlineKeyboardButton(text="➕ Зарегистрировать заявку", callback_data="set_request")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

    manager_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список заявок", callback_data="list_requests")],
            [InlineKeyboardButton(text="✅ Принять заявку", callback_data="accept_request")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

    inspector_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список заявок", callback_data="select_requests"),
             InlineKeyboardButton(text="📑 Выбор заявок", callback_data="inspector_accept")],
            [InlineKeyboardButton(text="✅ Одобрить", callback_data="approve_request"),
             InlineKeyboardButton(text="🚫 Отклонить", callback_data="reject_request")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

    if str(user_id) == await get_user(user_id):
        await message.answer(
            "📝 Привет, пользователь! Выберите действие:",
            reply_markup=user_kb
        )
    elif str(user_id) == await get_product_manager(user_id):
        await message.answer(
            "🏢 Здравствуйте, менеджер продукта! Что вы хотите сделать?",
            reply_markup=pm_kb
        )
    elif str(user_id) == await get_manager(user_id):
        await message.answer(
            "📋 Добрый день, менеджер! Выберите опцию:",
            reply_markup=manager_kb
        )
    elif str(user_id) == await get_inspector(user_id):
        await message.answer(
            "📑 Здравствуйте, инспектор! Готовы к проверке заявок?",
            reply_markup=inspector_kb
        )
    else:
        await message.answer("❗️ Вам нужно зарегистрироваться в боте.")


"""Модели для пользователей"""


@router.message(Command("reg"))
async def registration(message: types.Message):
    user_id = message.from_user.id
    if str(user_id) != await get_user(user_id):
        keyboard = await choose_company()
        if keyboard:
            await message.answer("Выберите компанию:", reply_markup=keyboard)
        else:
            await message.answer("Компании не найдены.")
    else:
        await message.answer("Вы уже зарегестрированы.")


@router.callback_query(lambda call: call.data.startswith("select_company:"))
async def process_company_selection(callback_query: CallbackQuery, state: FSMContext):
    comp_id = callback_query.data.split(':')[1]
    comp_name = await get_company_name(comp_id)
    user_id = callback_query.from_user.id
    user_range = 'users!A:B'
    values = [[str(user_id), comp_name]]

    service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=user_range,
        valueInputOption='RAW',
        body={'values': values}
    ).execute()

    await callback_query.message.edit_text(text=f"Вы зарегистрировали компанию ✅")
    await state.clear()


@router.callback_query(lambda call: call.data.startswith("request"))
async def process_user_apply_request(callback_query: types.CallbackQuery, state: FSMContext):
    text = (
        "<b>Введите следующую информацию через точку с запятой (;):</b>\n\n"
        "<code>"
        "1) APPLICATION №;\n"
        "2) The standard;\n"
        "3) Type of welding joint;\n"
        "4) VMC;\n"
        "5) UT;\n"
        "6) PT;\n"
        "7) RT;\n"
        "8) LT(cerosin);\n"
        "9) LT(vacuum)\n"
        "</code>"
    )
    await callback_query.message.edit_text(text, parse_mode="HTML")
    await state.set_state(Form.waiting_for_user_apply_request)


@router.message(Form.waiting_for_user_apply_request)
async def process_user_apply_request_save(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.replace("\n", " ").strip()
    parts = [p.strip() for p in text.split(";", maxsplit=8) if p.strip()]

    if len(parts) != 9:
        await message.answer("❌ Ошибка ввода. Нужно передать 9 значений через `;`.")
        await state.set_state(Form.waiting_for_user_apply_request)

    application, standard, joint_type, vmc, ut, pt, rt, ltc, ltv = parts
    if '/' in application:
        await message.answer("❌ Ошибка: в названии заявки недопустим символ `/`. Попробуйте снова ввести данные.")
        await state.set_state(Form.waiting_for_user_apply_request)

    company = await get_user_company(user_id)

    if not company:
        await message.answer("❌ Не удалось определить компанию. Пройдите регистрацию заново.")
        await state.clear()

    today = datetime.now().strftime("%d-%m-%y_%H:%M")
    output_path = await generate_application_excel(
        application, company, today, standard, joint_type, vmc, ut, pt, rt, ltc, ltv
    )

    await save_and_send_application(
        message, user_id, application, company, today, standard, joint_type, vmc, ut, pt, rt, ltc, ltv, output_path
    )
    if os.path.exists(output_path):
        os.remove(output_path)

    product_managers = await get_product_manager_all()
    if product_managers:
        for manager_id in product_managers:
            await message.bot.send_message(
                chat_id=manager_id,
                text=f'🆕 ОТДАТЬ В РАБОТУ НОВУЮ ЗАЯВКУ: <b>{application}</b> от компании: <b>{company}</b>, дата: <b>{today}</b>',
                parse_mode="HTML"
            )
    await state.clear()


@router.callback_query(lambda call: call.data.startswith("document"))
async def process_user_get_document_request(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if str(user_id) == await get_user(user_id):
        keyboard = await get_orders(user_id)
        if keyboard:
            await callback_query.message.edit_text("Выберите заказ:", reply_markup=keyboard)
        else:
            await callback_query.message.edit_text("Заказов не найдено.")
    else:
        await callback_query.message.edit_text("Вы не зарегестрированы.")


@router.callback_query(lambda call: call.data.startswith("chose_order:"))
async def process_get_document_selection(callback_query: CallbackQuery, state: FSMContext):
    str_id = int(callback_query.data.split(':')[1])
    user_range = 'journal!A:M'

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=user_range
    ).execute()
    values = result.get('values', [])

    if str_id >= len(values):
        await callback_query.message.answer("Ошибка: заказ не найден.")
        return

    row = values[str_id]
    if len(row) < 13:
        await callback_query.message.answer("Ошибка: файл не найден в заказе.")
        return

    file_id = row[12]

    await callback_query.message.edit_text(text="⏳ Загружаем файл...")

    drive_service = build('drive', 'v3', credentials=credentials)

    request = drive_service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)
    file_title = f"Заявка {row[1]}_{row[3]}.xlsx"

    document = BufferedInputFile(
        file_stream.read(),
        filename=file_title
    )

    await callback_query.message.answer_document(
        document=document,
        caption="Ваша заявка ✅"
    )

    await state.clear()


@router.callback_query(lambda call: call.data.startswith("status"))
async def process_user_get_document_request(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if str(user_id) == await get_user(user_id):
        keyboard = await get_order_status(user_id)
        if keyboard:
            await callback_query.message.edit_text("Выберите заказ:", reply_markup=keyboard)
        else:
            await callback_query.message.edit_text("Заказов не найдено.")
    else:
        await callback_query.message.edit_text("Вы не зарегестрированы.")


@router.callback_query(lambda call: call.data.startswith("order_status:"))
async def process_get_document_selection(callback_query: CallbackQuery, state: FSMContext):
    str_id = int(callback_query.data.split(':')[1])
    user_range = 'journal!A:R'

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=user_range
    ).execute()
    values = result.get('values', [])

    if str_id >= len(values):
        await callback_query.message.answer("Ошибка: заказ не найден.")
        return

    row = values[str_id]
    if len(row) < 13:
        await callback_query.message.answer("Ошибка: информация о статусе отсутствует.")
        return
    row += [''] * (18 - len(row))
    status = row[17]

    await state.clear()

    if status.strip():
        await callback_query.message.edit_text(text=f"📄 Статус заявки: {status}")
    else:
        await callback_query.message.edit_text(text="📄 Статус заявки: В обработке.")


"""Модели для продукт менеджеров"""


@router.message(Command("reg_p"))
async def registration_product_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if str(user_id) != await get_product_manager(user_id):
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_product_manager)
    else:
        await message.answer("Вы уже зарегестрированы в компании!")


@router.message(Form.waiting_for_reg_product_manager)
async def process_for_product_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    fio, password = message.text.split(",")
    fio = fio.strip()
    password = password.strip()
    if await get_product_manager_password() == password:
        values = [[str(user_id), fio]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='users!D:E',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        await message.answer(f"Вы зарегистрированы в компании как продукт-манеджер ✅")
        await state.clear()
    else:
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_product_manager)


@router.callback_query(lambda call: call.data.startswith("companies"))
async def process_user_get_document_request(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    if str(user_id) == await get_product_manager(user_id):
        keyboard = await get_manager_companies()
        if keyboard:
            await callback_query.message.edit_text("Выберите компанию, для просмотра заявок:", reply_markup=keyboard)
        else:
            await callback_query.message.edit_text("Заказов не найдено.")
    else:
        await callback_query.message.edit_text("Вы не зарегестрированы как промежуточный менеджер.")


@router.callback_query(lambda call: call.data.startswith("get_requests:"))
async def show_company_requests(callback_query: CallbackQuery):
    idx = int(callback_query.data.split(":")[1])

    company_range_name = 'companies!A:C'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=company_range_name
    ).execute()
    companies = result.get('values', [])

    if idx < 2 or idx >= len(companies):
        await callback_query.message.answer("Ошибка: компания не найдена.")
        return

    company_name = companies[idx][1]
    order_range_name = 'journal!A:M'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])
    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        if len(order) >= 3 and order[2] == company_name:
            request_name = order[1] if len(order) > 1 else "Без названия"
            buttons.append(
                types.InlineKeyboardButton(
                    text=request_name,
                    callback_data=f"selected_company:{order_idx}"
                )
            )

    if not buttons:
        await callback_query.message.edit_text("У этой компании нет заявок.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text=f"📄 Заявки компании *{company_name}*\:",
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )


@router.callback_query(lambda call: call.data.startswith("selected_company:"))
async def process_company_selection_for_manager(callback_query: CallbackQuery, state: FSMContext):
    idx = int(callback_query.data.split(':')[1])
    user_range = 'journal!A:M'
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=user_range
    ).execute()
    values = result.get('values', [])

    row = values[idx]
    if len(row) < 13:
        await callback_query.message.answer("Ошибка: файл не найден в заказе.")
        return

    file_id = row[12]

    await callback_query.message.edit_text(text="⏳ Загружаем файл...")

    drive_service = build('drive', 'v3', credentials=credentials)

    request = drive_service.files().get_media(fileId=file_id)
    file_stream = io.BytesIO()
    downloader = MediaIoBaseDownload(file_stream, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    file_stream.seek(0)
    file_title = f"Заявка {row[1]}_{row[3]}.xlsx"

    document = BufferedInputFile(
        file_stream.read(),
        filename=file_title
    )
    await callback_query.message.delete()
    await callback_query.message.answer_document(
        document=document,
        caption=f"Заявка {row[1]} от {row[3]}"
    )

    await state.clear()


@router.callback_query(lambda call: call.data == "set_request")
async def show_empty_requests(callback_query: CallbackQuery):
    order_range_name = 'journal!A:N'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])

    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        if len(order) <= 13 or order[13].strip() == '':
            request_name = order[1] if len(order) > 1 else "Без названия"
            buttons.append(
                types.InlineKeyboardButton(
                    text=request_name,
                    callback_data=f"assign_manager:{order_idx}"
                )
            )

    if not buttons:
        await callback_query.message.edit_text("Все заявки разобраны.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text="📄 Список заявок:",
        reply_markup=keyboard
    )


@router.callback_query(lambda call: call.data.startswith("assign_manager:"))
async def assign_product_manager_to_request(callback_query: CallbackQuery):
    order_idx = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    manager_name = await get_product_manager_name(user_id)
    if not manager_name:
        await callback_query.message.answer("Ошибка: не удалось определить ФИО менеджера.")
        return

    order_range_name = 'journal!A:N'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])

    if order_idx >= len(orders):
        await callback_query.message.answer("Ошибка: заявка не найдена.")
        return

    order = orders[order_idx]
    user_id_to_send = order[0] if len(order) > 1 else "Без названия"
    request_name = order[1] if len(order) > 1 else "Без названия"
    manager_cell = f'N{order_idx + 1}'
    status_cell = f'R{order_idx + 1}'
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'journal!{manager_cell}',
        valueInputOption='RAW',
        body={'values': [[manager_name]]}
    ).execute()

    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'journal!{status_cell}',
        valueInputOption='RAW',
        body={'values': [["В обработке"]]}
    ).execute()

    await callback_query.message.edit_text(f"✅ Вы назначены менеджером на заявку <b>{request_name}</b>",
                                           parse_mode="HTML")

    managers = await get_manager_all()
    if managers:
        for manager_id in managers:
            await callback_query.bot.send_message(
                chat_id=manager_id,
                text=f'🆕 Новая заявка: <b>{request_name}</b>',
                parse_mode="HTML"
            )
    await callback_query.bot.send_message(
        chat_id=int(user_id_to_send),
        text=f'Сменился статус заявки: <b>{request_name}</b>, на <b>"В обработке"</b>.',
        parse_mode="HTML"
    )

"""Модели для менеджеров"""


@router.message(Command("reg_m"))
async def registration_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if str(user_id) != await get_manager(user_id):
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_manager)
    else:
        await message.answer("Вы уже зарегестрированы в компании!")


@router.message(Form.waiting_for_reg_manager)
async def process_for_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    fio, password = message.text.split(",")
    fio = fio.strip()
    password = password.strip()
    if await get_manager_password() == str(password):
        values = [[str(user_id), fio]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='users!G:H',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        await message.answer(f"Вы зарегистрированы в компании как менеджер ✅")
        await state.clear()
    else:
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_manager)


@router.callback_query(lambda call: call.data == "list_requests")
async def show_all_open_requests(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    manager_name = await get_manager_name(user_id)
    manager_name = manager_name.strip()
    order_range_name = 'journal!A:S'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])
    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        order += [""] * (19 - len(order))
        if len(order) >= 19:
            assigned_manager = order[14].strip()
            if (assigned_manager == '' or assigned_manager == manager_name) and order[17].strip() == '':
                request_name = order[1] if len(order) > 1 else "Без названия"
                buttons.append(
                    types.InlineKeyboardButton(
                        text=request_name,
                        callback_data=f"selected_company:{order_idx}"
                    )
                )

    if not buttons:
        await callback_query.message.edit_text("Все заявки разобраны.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text="📄 Список заявок:",
        reply_markup=keyboard
    )


@router.callback_query(lambda call: call.data == "accept_request")
async def show_empty_requests_for_manager(callback_query: CallbackQuery):
    order_range_name = 'journal!A:O'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])
    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        if len(order) <= 15 or order[14].strip() == '':
            order += [""] * (15 - len(order))
            request_name = order[1] if len(order) > 1 else "Без названия"
            buttons.append(
                types.InlineKeyboardButton(
                    text=request_name,
                    callback_data=f"manager_assign:{order_idx}"
                )
            )

    if not buttons:
        await callback_query.message.edit_text("Нет заявок без менеджера.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text="📄 Список заявок:",
        reply_markup=keyboard
    )


@router.callback_query(lambda call: call.data.startswith("manager_assign:"))
async def assign_manager_to_request(callback_query: CallbackQuery):
    order_idx = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    manager_name = await get_manager_name(user_id)
    if not manager_name:
        await callback_query.message.answer("Ошибка: не удалось определить ФИО менеджера.")
        return

    order_range_name = 'journal!A:O'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])

    if order_idx >= len(orders):
        await callback_query.message.answer("Ошибка: заявка не найдена.")
        return

    order = orders[order_idx]
    user_id_to_send = order[0] if len(order) > 1 else "Без названия"
    request_name = order[1] if len(order) > 1 else "Без названия"

    cell_address = f'O{order_idx + 1}'
    status_cell = f'R{order_idx + 1}'
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'journal!{cell_address}',
        valueInputOption='RAW',
        body={'values': [[manager_name]]}
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'journal!{status_cell}',
        valueInputOption='RAW',
        body={'values': [["Назначен менеджер"]]}
    ).execute()

    await callback_query.message.edit_text(f"✅ Вы назначены менеджером на заявку <b>{request_name}</b>",
                                           parse_mode="HTML")
    inspectors = await get_inspector_all()
    if inspectors:
        for inspector_id in inspectors:
            await callback_query.bot.send_message(
                chat_id=inspector_id,
                text=f'🆕 Новая заявка: <b>{request_name}</b>',
                parse_mode="HTML"
            )
    product_managers = await get_product_manager_all()
    if product_managers:
        for product_manager_id in product_managers:
            await callback_query.bot.send_message(
                chat_id=product_manager_id,
                text=f'Заявка <b>{request_name}</b> принята менеджером.',
                parse_mode="HTML"
            )
    await callback_query.bot.send_message(
        chat_id=int(user_id_to_send),
        text=f'Сменился статус заявки: <b>{request_name}</b>, на <b>"Назначен менеджер"</b>.',
        parse_mode="HTML"
    )

"""Модели для контролеров"""


@router.message(Command("reg_c"))
async def registration_inspector(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if str(user_id) != await get_inspector(user_id):
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_inspector)
    else:
        await message.answer("Вы уже зарегестрированы в компании!")


@router.message(Form.waiting_for_reg_inspector)
async def process_for_inspector(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    fio, password = message.text.split(",")
    fio = fio.strip()
    password = password.strip()
    if await get_inspector_password() == password:
        values = [[str(user_id), fio]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='users!J:K',
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
        await message.answer(f"Вы зарегистрированы в компании как инспектор ✅")
        await state.clear()
    else:
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_inspector)


@router.callback_query(lambda call: call.data == "select_requests")
async def show_all_open_requests_for_inspector(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    manager_name = await get_inspector_name(user_id)
    manager_name = manager_name.strip()
    order_range_name = 'journal!A:S'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])
    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        order += [""] * (19 - len(order))
        if len(order) >= 19:
            assigned_manager = order[15].strip()
            if (assigned_manager == '' or assigned_manager == manager_name) and order[17].strip() == '':
                request_name = order[1] if len(order) > 1 else "Без названия"
                buttons.append(
                    types.InlineKeyboardButton(
                        text=request_name,
                        callback_data=f"selected_company:{order_idx}"
                    )
                )

    if not buttons:
        await callback_query.message.edit_text("Все заявки разобраны.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text="📄 Список заявок:",
        reply_markup=keyboard
    )


@router.callback_query(lambda call: call.data == "inspector_accept")
async def show_empty_requests_for_manager(callback_query: CallbackQuery):
    order_range_name = 'journal!A:P'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])
    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        if len(order) <= 16 or order[15].strip() == '':
            order += [""] * (16 - len(order))
            request_name = order[1] if len(order) > 1 else "Без названия"
            buttons.append(
                types.InlineKeyboardButton(
                    text=request_name,
                    callback_data=f"ins_assign:{order_idx}"
                )
            )

    if not buttons:
        await callback_query.message.edit_text("Все заявки разобраны.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text="📄 Список заявок:",
        reply_markup=keyboard
    )


@router.callback_query(lambda call: call.data.startswith("ins_assign:"))
async def assign_manager_to_request(callback_query: CallbackQuery):
    order_idx = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    manager_name = await get_inspector_name(user_id)
    if not manager_name:
        await callback_query.message.answer("Ошибка: не удалось определить ФИО менеджера.")
        return

    order_range_name = 'journal!A:P'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])

    if order_idx >= len(orders):
        await callback_query.message.answer("Ошибка: заявка не найдена.")
        return

    order = orders[order_idx]
    user_id_to_send = order[0] if len(order) > 1 else "Без названия"
    request_name = order[1] if len(order) > 1 else "Без названия"

    cell_address = f'P{order_idx + 1}'
    status_cell = f'R{order_idx + 1}'
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'journal!{cell_address}',
        valueInputOption='RAW',
        body={'values': [[manager_name]]}
    ).execute()
    service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f'journal!{status_cell}',
        valueInputOption='RAW',
        body={'values': [["В работе"]]}
    ).execute()

    await callback_query.message.edit_text(f"✅ Вы назначены инспектором на заявку <b>{request_name}</b>",
                                           parse_mode="HTML")
    managers = await get_manager_all()
    if managers:
        for manager_id in managers:
            await callback_query.bot.send_message(
                chat_id=manager_id,
                text=f'Инспектор взялся за заявку: <b>{request_name}.</b>',
                parse_mode="HTML"
            )
    product_managers = await get_product_manager_all()
    if product_managers:
        for product_manager_id in product_managers:
            await callback_query.bot.send_message(
                chat_id=product_manager_id,
                text=f'Инспектор взялся за заявку <b>{request_name}</b>.',
                parse_mode="HTML"
            )
    await callback_query.bot.send_message(
        chat_id=int(user_id_to_send),
        text=f'Сменился статус заявки: <b>{request_name}</b>, на <b>"В работе"</b>.',
        parse_mode="HTML"
    )


@router.callback_query(lambda call: call.data == "approve_request")
async def show_empty_requests_for_manager(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    manager_name = await get_inspector_name(user_id)
    manager_name = manager_name.strip()
    order_range_name = 'journal!A:Q'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])
    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        order += [""] * (18 - len(order))
        if len(order) >= 18 and order[17].strip() == '':
            assigned_manager = order[16].strip()
            if assigned_manager == '' or assigned_manager == manager_name:
                request_name = order[1] if len(order) > 1 else "Без названия"
                buttons.append(
                    types.InlineKeyboardButton(
                        text=request_name,
                        callback_data=f"app_request:{order_idx}"
                    )
                )

    if not buttons:
        await callback_query.message.edit_text("У вас нет заявок на подтвержение.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text="📄 Список заявок:",
        reply_markup=keyboard
    )


@router.callback_query(lambda call: call.data.startswith("app_request:"))
async def assign_manager_to_request(callback_query: CallbackQuery):
    order_idx = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    manager_name = await get_inspector_name(user_id)
    if not manager_name:
        await callback_query.message.answer("Ошибка: не удалось определить ФИО менеджера.")
        return

    order_range_name = 'journal!A:P'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])

    if order_idx >= len(orders):
        await callback_query.message.answer("Ошибка: заявка не найдена.")
        return

    order = orders[order_idx]
    user_id_to_send = order[0] if len(order) > 1 else "Без названия"
    request_name = order[1] if len(order) > 1 else "Без названия"
    application = order[1] if len(order) > 1 else "Без названия"
    today = order[3] if len(order) > 3 else "Без даты"
    manager = order[14] if len(order) > 14 else "Без менеджера"

    template_path = "templates/Отчет.xlsx"
    output_path = f"output/Отчет_{application}_{today}.xlsx"
    copyfile(template_path, output_path)
    file_id = upload_report(output_path)
    status_cell = f'R{order_idx + 1}'
    data_cell = f'Q{order_idx + 1}'
    file_id_cell = f'S{order_idx + 1}'

    finished_date = str(datetime.now().strftime("%d-%m-%y %H:%M"))

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            'valueInputOption': 'RAW',
            'data': [
                {'range': f'journal!{status_cell}', 'values': [["Выполнено"]]},
                {'range': f'journal!{data_cell}', 'values': [[finished_date]]},
                {'range': f'journal!{file_id_cell}', 'values': [[file_id]]},
            ]
        }
    ).execute()
    await callback_query.message.edit_text(
        f"✅ Вы выполнили заявку <b>{request_name}</b>",
        parse_mode="HTML"
    )

    manager_id = await get_manager_id(manager)
    product_managers = await get_product_manager_all()
    if product_managers:
        for product_manager_id in product_managers:
            await callback_query.bot.send_message(
                chat_id=product_manager_id,
                text=f'Инспектор ввыполнил заявку <b>{request_name}.</b>',
                parse_mode="HTML"
            )
    input_file = FSInputFile(output_path)
    if manager_id:
        await callback_query.bot.send_document(
            chat_id=int(manager_id),
            document=input_file,
            caption=f'📄 Отчет по заявке <b>{request_name}</b>.',
            parse_mode="HTML"
        )
    await callback_query.bot.send_document(
        chat_id=int(user_id_to_send),
        document=input_file,
        caption=f'📄 Отчет по заявке <b>{request_name}</b>.',
        parse_mode="HTML"
    )
    if os.path.exists(output_path):
        os.remove(output_path)


@router.callback_query(lambda call: call.data == "reject_request")
async def show_empty_requests_for_manager(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    manager_name = await get_inspector_name(user_id)
    manager_name = manager_name.strip()
    order_range_name = 'journal!A:Q'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])
    buttons = []
    for order_idx, order in enumerate(orders[2:], start=2):
        order += [""] * (18 - len(order))
        if len(order) >= 18 and order[17].strip() == '':
            assigned_manager = order[16].strip()
            if assigned_manager == '' or assigned_manager == manager_name:
                request_name = order[1] if len(order) > 1 else "Без названия"
                buttons.append(
                    types.InlineKeyboardButton(
                        text=request_name,
                        callback_data=f"rej_request:{order_idx}"
                    )
                )

    if not buttons:
        await callback_query.message.edit_text("У вас нет заявок чтобы отклонить их.")
        return

    inline_keyboard = [[btn] for btn in buttons]
    inline_keyboard.append([
        types.InlineKeyboardButton(
            text="❌ Закрыть",
            callback_data="close"
        )
    ])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

    await callback_query.message.edit_text(
        text="📄 Список заявок:",
        reply_markup=keyboard
    )


@router.callback_query(lambda call: call.data.startswith("rej_request:"))
async def assign_manager_to_request(callback_query: CallbackQuery):
    order_idx = int(callback_query.data.split(":")[1])
    user_id = callback_query.from_user.id

    manager_name = await get_inspector_name(user_id)
    if not manager_name:
        await callback_query.message.answer("Ошибка: не удалось определить ФИО менеджера.")
        return

    order_range_name = 'journal!A:P'
    order_result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=order_range_name
    ).execute()
    orders = order_result.get('values', [])

    if order_idx >= len(orders):
        await callback_query.message.answer("Ошибка: заявка не найдена.")
        return

    order = orders[order_idx]
    user_id_to_send = order[0] if len(order) > 1 else "Без названия"
    request_name = order[1] if len(order) > 1 else "Без названия"
    #application = order[1] if len(order) > 1 else "Без названия"
    #today = order[3] if len(order) > 3 else "Без даты"
    manager = order[14] if len(order) > 14 else "Без менеджера"

    #template_path = "templates/Отчет.xlsx"
    #output_path = f"output/Отчет_{application}_{today}.xlsx"
    #copyfile(template_path, output_path)
    #file_id = upload_report(output_path)
    status_cell = f'R{order_idx + 1}'
    data_cell = f'Q{order_idx + 1}'
    #file_id_cell = f'S{order_idx + 1}'

    finished_date = str(datetime.now().strftime("%d-%m-%y %H:%M"))

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            'valueInputOption': 'RAW',
            'data': [
                {'range': f'journal!{status_cell}', 'values': [["Отклонена"]]},
                {'range': f'journal!{data_cell}', 'values': [[finished_date]]},
                #{'range': f'journal!{file_id_cell}', 'values': [[file_id]]},
            ]
        }
    ).execute()
    await callback_query.message.edit_text(
        f"✅ Вы отклонили заявку <b>{request_name}</b>",
        parse_mode="HTML"
    )

    manager_id = await get_manager_id(manager)
    product_managers = await get_product_manager_all()
    if product_managers:
        for product_manager_id in product_managers:
            await callback_query.bot.send_message(
                chat_id=product_manager_id,
                text=f'❌ Инспектор отклонил заявку <b>{request_name}.</b>',
                parse_mode="HTML"
            )
    #input_file = FSInputFile(output_path)
    if manager_id:
        await callback_query.bot.send_message(
            chat_id=int(manager_id),
            #document=input_file,
            text=f'❌ Заявка отклонена <b>{request_name}</b>.',
            parse_mode="HTML"
        )
    await callback_query.bot.send_message(
        chat_id=int(user_id_to_send),
        #document=input_file,
        text=f'❌ Заявка отклонена <b>{request_name}</b>.',
        parse_mode="HTML"
    )
    #if os.path.exists(output_path):
        #os.remove(output_path)
