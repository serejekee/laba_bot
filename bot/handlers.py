from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import types, Router, F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, FSInputFile, InputMediaPhoto, InputMediaAnimation, \
    Message
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from datetime import datetime
from dateutil.relativedelta import relativedelta
from utils import get_user, get_manager, get_product_manager, get_inspector, spreadsheet_id, service, choose_company, \
    get_product_manager_password, get_manager_password, get_inspector_password, get_user_company, upload_to_drive, \
    get_company_name

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


@router.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id

    user_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="apply_request")],
            [InlineKeyboardButton(text="📤 Загрузить документ", callback_data="upload_document")],
            [InlineKeyboardButton(text="🔍 Статус заявки", callback_data="check_status")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

    pm_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏢 Список компаний", callback_data="pm_list_companies")],
            [InlineKeyboardButton(text="📋 Просмотр заявок", callback_data="pm_view_requests")],
            [InlineKeyboardButton(text="➕ Зарегистрировать заявку", callback_data="pm_register_request")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

    manager_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Список заявок", callback_data="mgr_list_requests")],
            [InlineKeyboardButton(text="🔍 Просмотр заявки", callback_data="mgr_view_request")],
            [InlineKeyboardButton(text="✅ Принять заявку", callback_data="mgr_accept_request")],
            [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")],
        ]
    )

    inspector_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📑 Выбор заявок", callback_data="insp_select_requests")],
            [InlineKeyboardButton(text="📂 Файлы заявок", callback_data="insp_request_files")],
            [
                InlineKeyboardButton(text="✅ Одобрено", callback_data="insp_approve_request"),
                InlineKeyboardButton(text="🚫 Отклонено", callback_data="insp_reject_request")
            ],
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
        insertDataOption='INSERT_ROWS',
        body={'values': values}
    ).execute()

    await callback_query.message.edit_text(text=f"Вы зарегистрировали компанию ✅")
    await state.clear()


@router.callback_query(lambda call: call.data.startswith("apply_request"))
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
    parts = [p.strip() for p in text.split(";", maxsplit=8)]
    parts = [p for p in parts if p]

    if len(parts) != 9:
        await message.answer(
            "Ошибка ввода. Убедитесь, что вы передали **9** значений, разделённых точкой с запятой (;).",
            parse_mode="Markdown"
        )
        return

    application, standard, joint_type, vmc, ut, pt, rt, ltc, ltv = parts

    company = await get_user_company(user_id)
    if not company:
        await message.answer("Не удалось определить компанию. Пожалуйста, зарегистрируйтесь заново.")
        await state.clear()
        return

    today = datetime.today().strftime("%d-%m-%y_%H:%M")
    template_path = "templates/Заявка.html"
    output_path = f"output/Заявка_{application}_{today}.html"

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    data_map = {"application": application, "company": company, "today": today, "standard": standard,
                "joint_type": joint_type, "vmc": vmc, "ut": ut, "pt": pt, "rt": rt, "ltc": ltc, "ltv": ltv, }
    for key, val in data_map.items():
        template = template.replace(f"{{{key}}}", val)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(template)

    file_id = upload_to_drive(output_path)
    input_file = types.FSInputFile(output_path)
    if file_id:
        values = [[str(user_id), application, company, today, standard, joint_type, vmc, ut, pt, rt, ltc, ltv, file_id]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='journal!A3:M',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()

        await message.answer_document(input_file,
                                      caption="Ваша заявка успешно сформирована ✅")
    else:
        await message.answer("Произошла ошибка при загрузке файла на Google Диск.")

    await state.clear()


"""Модели для продукт менеджеров"""


@router.message(Command("reg_p"))
async def registration_product_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if str(user_id) != await get_product_manager(user_id):
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_product_manager)
    else:
        await message.answer("Вы уде зарегестрированы в компании!")


@router.callback_query(Form.waiting_for_reg_product_manager)
async def process_for_product_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    password = []
    fio = []
    if user_id:
        fio, password = message.text.split(",")
    if await get_product_manager_password() == password:
        values = [[str(user_id), fio]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='users!D:E',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        await message.answer(f"Документ отправлен на расмотрение, скоро с вами свяжутся")
        await state.clear()
    else:
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_product_manager)


"""Модели для менеджеров"""


@router.message(Command("reg_m"))
async def registration_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if str(user_id) != await get_manager(user_id):
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_manager)
    else:
        await message.answer("Вы уже зарегестрированы в компании!")


@router.callback_query(Form.waiting_for_reg_manager)
async def process_for_manager(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    password = []
    fio = []
    if user_id:
        fio, password = message.text.split(",")
    if await get_manager_password() == password:
        values = [[str(user_id), fio]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='users!G:H',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        await message.answer(f"Вы зарегистрированы в компании как менеджер ✅")
        await state.clear()
    else:
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_manager)


"""Модели для контролеров"""


@router.message(Command("reg_c"))
async def registration_inspector(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if str(user_id) != await get_inspector(user_id):
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_inspector)
    else:
        await message.answer("Вы уже зарегестрированы в компании!")


@router.callback_query(Form.waiting_for_reg_inspector)
async def process_for_inspector(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    password = []
    fio = []
    if user_id:
        fio, password = message.text.split(",")
    if await get_inspector_password() == password:
        values = [[str(user_id), fio]]
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range='users!G:H',
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': values}
        ).execute()
        await message.answer(f"Вы зарегистрированы в компании как инспектор ✅")
        await state.clear()
    else:
        await message.answer("Введите ФИО и пароль, через запятую:")
        await state.set_state(Form.waiting_for_reg_inspector)
