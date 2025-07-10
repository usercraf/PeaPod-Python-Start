from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db_file import cur, base

from log_file import logger
from key_file import buttons_students, get_home_builder


students_router = Router()

class Verification(StatesGroup):
    verification = State()

def get_paginated_keyboard(students: list, page: int, per_page: int = 5) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    start = page * per_page
    end = start + per_page
    page_students = students[start:end]

    for id_hw in page_students:
        button_text = f"Домашнє завдання № {id_hw}"
        builder.add(types.InlineKeyboardButton(text=button_text, callback_data=f"selecthw_{id_hw}"))
    builder.adjust(1)
    navigation = []
    if page > 0:
        navigation.append(types.InlineKeyboardButton(text="⬅️", callback_data=f"page_{page - 1}"))
    if end < len(students):
        navigation.append(types.InlineKeyboardButton(text="➡️", callback_data=f"page_{page + 1}"))

    if navigation:
        builder.row(*navigation)

    return builder.as_markup()


@students_router.callback_query(F.data == 'verification')
async def verification_student(callback: types.CallbackQuery, state: FSMContext):
    logger.info(
        f"Користувач {callback.from_user.first_name} (ID: {callback.from_user.id}) хоче пройти верифікацію.")
    await callback.message.answer('⬇️ Надішліть свій код для верифікації')
    await state.set_state(Verification.verification)


@students_router.message(Verification.verification)
async def verification_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    try:
        secret_code = cur.execute("""SELECT 1 FROM students WHERE secret_key=?""", (code,)).fetchone()
        if secret_code is None:
            logger.warning(
                f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) ввів непривильний пароль до верифікації.")
            await message.answer('❌ Ви ввели невірний код. Спробуйте ще раз')
            await state.set_state(Verification.verification)
        else:
            logger.info(
                f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) пройшов верифікацію.")

            cur.execute("""UPDATE students SET verification=?, tg_id=? WHERE secret_key=?""", (1, int(message.from_user.id), code))
            base.commit()
            await state.clear()
            await message.answer('🥳 Вітаю верифікація пройдена.Натисніть /start.')

    except Exception as e:
        logger.error(f"[DB] Помилка під час SELECT: {e} функція - verification_code")
        await message.answer("⚠️ Помилка бази даних. "
                             "Спробуйте пізніше або зверніться до адміністратора.", reply_markup=get_home_builder().as_markup())
        await state.clear()


@students_router.callback_query(F.data == 'chek_stars')
async def chek_my_stars(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for key, value in buttons_students().items():
        builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
    builder.adjust(1)
    try:
        data_stars = cur.execute("""SELECT points FROM students WHERE tg_id=?""", (callback.from_user.id,)).fetchone()
        await callback.message.answer(f'{callback.from_user.first_name} на Вашому рахунку {data_stars[0]} 🌟.',
                                      reply_markup=builder.as_markup())
    except Exception as e:
        logger.error(f'Помилка {e} під час перевірки наявності зірок у користувача {callback.from_user.id}')
        await callback.message.edit_text('❌ Сталася помилка, зверніться до адміністратора.',
                                         reply_markup=builder.as_markup())


@students_router.callback_query(F.data == "home_work_students")
async def show_hw_students(callback: types.CallbackQuery):
    hw_data = cur.execute("SELECT id FROM hw_table").fetchall()
    hw_list = [item[0] for item in hw_data]
    keyboard = get_paginated_keyboard(hw_list, page=0)
    await callback.message.answer("Перелік домашнього завдання:", reply_markup=keyboard)


@students_router.callback_query(F.data.startswith("page_"))
async def paginate_students(callback: types.CallbackQuery):
    page = int(callback.data.split("_")[1])
    hw_data = cur.execute("SELECT id FROM hw_table").fetchall()
    hw_list = [item[0] for item in hw_data]
    keyboard = get_paginated_keyboard(hw_list, page)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@students_router.callback_query(F.data.startswith('selecthw_'))
async def get_hw(callback: types.CallbackQuery):
    id_hw = callback.data.split('_')[1]
    data_hw = cur.execute("""SELECT home_work, day_of FROM hw_table WHERE id=?""",(id_hw,)).fetchone()
    await callback.bot.send_message(chat_id=callback.from_user.id, text=f'{data_hw[0]}\n\nДата здачі завдання: {data_hw[1]}')
    await callback.answer()