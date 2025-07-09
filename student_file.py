from aiogram import types, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db_file import cur, base

from log_file import logger
from key_file import buttons_students


students_router = Router()

class Verification(StatesGroup):
    verification = State()

@students_router.callback_query(F.data == 'verification')
async def verification_student(callback: types.CallbackQuery, state: FSMContext):
    logger.info(
        f"Користувач {callback.from_user.first_name} (ID: {callback.from_user.id}) хоче пройти верифікацію.")
    await callback.message.answer('⬇️ Надішліть свій код для верифікації')
    await state.set_state(Verification.verification)


@students_router.message(Verification.verification)
async def verification_code(message: types.Message, state: FSMContext):
    code = message.text.strip()
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🏠 На головну", callback_data="Home"))
    try:
        secret_code = cur.execute("""SELECT 1 FROM students WHERE secret_key=?""", (code,)).fetchone()
        if secret_code is None:
            logger.warning(
                f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) ввів непривильний пароль до верифікації.")
            await message.answer('❌ Ви ввели певірний код. Спробуйте ще раз')
            await state.set_state(Verification.verification)
        else:
            logger.info(
                f"Користувач {message.from_user.first_name} (ID: {message.from_user.id}) пройшов верифікацію.")

            cur.execute("""UPDATE students SET verification=?, tg_id=? WHERE secret_key=?""", (1, int(message.from_user.id), code))
            base.commit()
            await state.clear()
            await message.answer('🥳 Вітаю верифікація пройдена')
    except Exception as e:
        logger.error(f"[DB] Помилка під час SELECT: {e} функція - verification_code")
        await message.answer("⚠️ Помилка бази даних. "
                             "Спробуйте пізніше або зверніться до адміністратора.", reply_markup=builder.as_markup())
        await state.clear()


@students_router.callback_query(F.data == 'chek_start')
async def chek_my_stars(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for key, value in buttons_students().items():
        builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
    builder.adjust(1)
    try:
        data_stars = cur.execute("""SELECT points FROM students WHERE tg_id=?""", (callback.from_user.id,)).fetchone()
        await callback.message.edit_text(f'{callback.from_user.first_name} на Вашому рахунку {data_stars[0]} 🌟.',
                                      reply_markup=builder.as_markup())
    except Exception as e:
        logger.error(f'Помилка {e} під час перевірки наявності зірок у користувача {callback.from_user.id}')
        await callback.message.edit_text('❌ Сталася помилка, зверніться до адміністратора.',
                                         reply_markup=builder.as_markup())

