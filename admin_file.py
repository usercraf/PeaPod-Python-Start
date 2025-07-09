from aiogram import types, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db_file import cur, base
import random

from log_file import logger

admin_router = Router()

class AddStudent(StatesGroup):
    name = State()

class AddStars(StatesGroup):
    one_student = State()
    get_stars = State()
    record_to_db = State()

def generate_unique_code():
    while True:
        code = "{:06d}".format(random.randint(100000, 999999))
        exists = cur.execute("SELECT 1 FROM students WHERE secret_key = ?", (code,)).fetchone()
        if not exists:
            return int(code)


@admin_router.callback_query(F.data == 'add_student')
async def get_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('⬇️ Введіть імʼя студента.')
    await state.set_state(AddStudent.name)

@admin_router.message(AddStudent.name)
async def record_student(message: types.Message, state: FSMContext):
    name_student = message.text.strip()
    secret_key = generate_unique_code()
    try:
        cur.execute("""INSERT INTO students (full_name, secret_key) VALUES (?,?)""", (name_student, secret_key))
        base.commit()
        logger.info(f'Студента {name_student} успішно додано до бази даних.')
        await message.answer(f'✅ Студента {name_student} внесено до бази даних.\n{secret_key} його ключ верифікації.')
        await state.clear()

    except Exception as e:
        logger.error(f'Виникла помилка при додаванні студента в базу даних {e}')
        await message.answer('❌ Виникли проблеми з базою даних. Дивіться логи.')


@admin_router.callback_query(F.data == 'add_stars')
async def all_students(callback: types.CallbackQuery, state: FSMContext):
    try:
        data_students = cur.execute("""SELECT full_name, tg_id FROM students WHERE role=?""", ('student',)).fetchall()
        builder = InlineKeyboardBuilder()
        for name, tg_id in data_students:
            builder.add(types.InlineKeyboardButton(text=name, callback_data=f'student_{tg_id}'))
        builder.adjust(1)
        await callback.message.answer('⬇️ Виберіть студента.', reply_markup=builder.as_markup())
        await state.set_state(AddStars.one_student)
    except Exception as e:
        logger.error(f'Сталась помилка {e} під час читання бази даних у функції all_students')
        await callback.message.answer(text='❌ Сталась помилка зверніться до адміністратора.')
        await state.clear()

@admin_router.callback_query(AddStars.one_student, F.data.startswith('student_'))
async def get_stars(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tg_id=callback.data.split("_")[1])
    await callback.message.answer('⬇️ Введіть кількість зірок яку маємо додати.')
    await state.set_state(AddStars.get_stars)

@admin_router.message(AddStars.get_stars)
async def record_to_table(message: types.Message, state: FSMContext):
    stars = int(message.text.strip())
    data_fsm = await state.get_data()
    tg_id = data_fsm.get('tg_id')
    try:
        get_stars = cur.execute("""SELECT points FROM students WHERE tg_id = ?""", (tg_id,)).fetchone()
        logger.info(f'Вибір кількості зірок у користувача {tg_id}')
        result_stars = int(get_stars[0]) + stars
        cur.execute("""UPDATE students SET points = ? WHERE tg_id = ?""", (result_stars, tg_id))
        base.commit()
        await message.answer('✅ Ви успішно додали зірочки до користувача. Користувачу буде надіслано повідомлення про оновлення.')
        try:
            await message.bot.send_message(chat_id=tg_id, text=f'Вам нараховано {stars} зірочок. Так тримати!')
        except TelegramBadRequest as e:
            logger.error(f'Користувач {tg_id} видалив чат або бот не має дозволу писати')
            await message.answer('❌ Сталась помилка зверніться до адміністратора.')
        except TelegramForbiddenError as e:
            logger.error(f'Користувач {tg_id} заблокував бота')
            await message.answer('❌ Сталась помилка зверніться до адміністратора.')

    except Exception as e:
        logger.error(f'Помилка {e} при роботи з БД функція record_to_table')
        await message.answer('❌ Сталася помилка, зверніться до адміністратора.')
        await state.clear()

