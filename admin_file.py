from aiogram import types, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from db_file import cur, base
import random

from log_file import logger
from key_file import get_home_builder

admin_router = Router()

class AddStudent(StatesGroup):
    name = State()

class AddStars(StatesGroup):
    one_student = State()
    get_stars = State()
    record_to_db = State()

class DellStudent(StatesGroup):
    del_student = State()

class AddHomeWork(StatesGroup):
    add_hw = State()
    record_to_db = State()


def generate_unique_code():
    while True:
        code = "{:06d}".format(random.randint(100000, 999999))
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            cur.execute("SELECT 1 FROM students WHERE secret_key = %s", (code,))
            exists = cur.fetchone()
        if not exists:
            return int(code)



@admin_router.callback_query(F.data == 'add_student')
async def get_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('⬇️ Введіть імʼя студента.', reply_markup=get_home_builder().as_markup())
    await state.set_state(AddStudent.name)

@admin_router.message(AddStudent.name)
async def record_student(message: types.Message, state: FSMContext):
    name_student = message.text.strip()
    secret_key = generate_unique_code()
    try:
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            cur.execute("""INSERT INTO students (full_name, secret_key) VALUES (%s,%s)""", (name_student, secret_key))
            base.commit()
        logger.info(f'Студента {name_student} успішно додано до бази даних.')
        await message.answer(f'✅ Студента {name_student} внесено до бази даних.\n{secret_key} ось ключ верифікації.',
                             reply_markup=get_home_builder().as_markup())
        await state.clear()

    except Exception as e:
        logger.error(f'Виникла помилка при додаванні студента в базу даних {e}')
        await message.answer('❌ Виникли проблеми з базою даних. Дивіться Log.',
                             reply_markup=get_home_builder().as_markup())

@admin_router.callback_query(F.data == 'add_stars')
async def all_students(callback: types.CallbackQuery, state: FSMContext):
    try:
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            cur.execute("""SELECT full_name, tg_id FROM students WHERE role=%s""", ('student',))
            data_students = cur.fetchall()
        builder = InlineKeyboardBuilder()
        for name, tg_id in data_students:
            builder.add(types.InlineKeyboardButton(text=name, callback_data=f'student_{tg_id}'))
        builder.adjust(1)
        await callback.message.answer('⬇️ Виберіть студента.', reply_markup=builder.as_markup())
        await state.set_state(AddStars.one_student)
    except Exception as e:
        logger.error(f'Сталась помилка {e} під час читання бази даних у функції all_students')
        await callback.message.answer(text='❌ Сталась помилка зверніться до адміністратора.',
                                      reply_markup=get_home_builder().as_markup())
        await state.clear()

@admin_router.callback_query(AddStars.one_student, F.data.startswith('student_'))
async def get_stars(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(tg_id=callback.data.split("_")[1])
    await callback.message.answer('⬇️ Введіть кількість зірок яку маємо додати.', reply_markup=get_home_builder().as_markup())
    await state.set_state(AddStars.get_stars)

@admin_router.message(AddStars.get_stars)
async def record_to_table(message: types.Message, state: FSMContext):
    stars = int(message.text.strip())
    data_fsm = await state.get_data()
    tg_id = data_fsm.get('tg_id')
    try:
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            cur.execute("""SELECT points FROM students WHERE tg_id = %s""", (tg_id,))
            get_star = cur.fetchone()
        logger.info(f'Вибір кількості зірок у користувача {tg_id}')
        result_stars = int(get_star[0]) + stars

        with base.cursor() as cur:
            cur.execute("""UPDATE students SET points = %s WHERE tg_id = %s""", (result_stars, tg_id))
            base.commit()
        await message.answer('✅ Ви успішно додали зірочки до користувача. '
                             'Користувачу буде надіслано повідомлення про оновлення.', reply_markup=get_home_builder().as_markup())
        try:
            await message.bot.send_message(chat_id=tg_id, text=f'Вам нараховано {stars} зірочок. Так тримати!')
        except TelegramBadRequest as e:
            logger.error(f'Користувач {tg_id} видалив чат або бот не має дозволу писати {e}.')
            await message.answer(f'❌ Сталась помилка зверніться до адміністратора {e}.')
        except TelegramForbiddenError as e:
            logger.error(f'Користувач {tg_id} заблокував бота {e}')
            await message.answer(f'❌ Сталась помилка зверніться до адміністратора {e}.')

    except Exception as e:
        logger.error(f'Помилка {e} при роботи з БД функція record_to_table')
        await message.answer('❌ Сталася помилка, зверніться до адміністратора.')
        await state.clear()

@admin_router.callback_query(F.data == 'del_student')
async def chose_dell_student(callback: types.CallbackQuery, state: FSMContext):
    try:
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            cur.execute("""SELECT full_name, tg_id FROM students WHERE role=%s""", ('student',))
            data_students = cur.fetchall()
        builder = InlineKeyboardBuilder()
        for name, tg_id in data_students:
            builder.add(types.InlineKeyboardButton(text=name, callback_data=f'dell_{tg_id}'))
        builder.adjust(1)
        await callback.message.answer('⬇️ Виберіть студента.', reply_markup=builder.as_markup())
        await state.set_state(DellStudent.del_student)
    except Exception as e:
        logger.error(f'Сталась помилка {e} під час читання бази даних у функції all_students')
        await callback.message.answer(text='❌ Сталась помилка зверніться до адміністратора.')
        await state.clear()

@admin_router.callback_query(DellStudent.del_student, F.data.startswith('dell_'))
async def del_student(callback: types.CallbackQuery, state: FSMContext):
    tg_id_user = callback.data.split('_')[1]
    try:
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            cur.execute("""DELETE FROM students WHERE tg_id = %s""", (tg_id_user,))
            logger.info(f'Відбулось видалення користувача {tg_id_user} з бази даних')
            base.commit()
        await callback.message.answer('✅ Успішно видалили студента.', reply_markup=get_home_builder().as_markup())
        await state.clear()
    except Exception as e:
        logger.error(f'Відбулась помилка {e} при видаленні студента.')
        await callback.message.answer(f'❌ Відбулась помилка.', reply_markup=get_home_builder().as_markup())
        await state.clear()


@admin_router.callback_query(F.data == 'add_home_work')
async def add_hw(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer('⬇️ Надішліть домашнє завдання.',
                                  reply_markup=get_home_builder().as_markup())
    await state.set_state(AddHomeWork.add_hw)

@admin_router.message(AddHomeWork.add_hw)
async def add_day_of(message: types.Message, state: FSMContext):
    await state.update_data(home_work = message.text)
    await message.answer('⬇️ Введіть дату до якої студенти мають виконати домашнє завдання.',
                         reply_markup=get_home_builder().as_markup())
    await state.set_state(AddHomeWork.record_to_db)

@admin_router.message(AddHomeWork.record_to_db)
async def record_hw(message: types.Message, state: FSMContext):
    day_of = message.text
    exercise = await state.get_data()
    home_work = exercise.get('home_work')
    try:
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            cur.execute("""INSERT INTO hw_table (home_work, day_of) VALUES (%s,%s)""", (home_work, day_of))
            base.commit()
        logger.info('Домашнє завдання було успішно внесено до бази даних.')
        await message.answer('✅ Ви успішно внесли завдання до бази даних.')
        await state.clear()
        try:
            cur.execute("""SELECT tg_id FROM students""")
            tg_id_students = cur.fetchall()
            for item in tg_id_students:
                await message.bot.send_message(chat_id=item[0], text='‼️ Додано нове домашнє завдання')
        except TelegramBadRequest as e:
            logger.error(f'Розсилка сповіщення про ДЗ. Користувач видалив чат або бот не має дозволу писати {e}.')
            await message.answer(f'❌ Сталась помилка зверніться до адміністратора {e}.')
        except TelegramForbiddenError as e:
            logger.error(f'Розсилка сповіщення про ДЗ. Користувач заблокував бота {e}')
            await message.answer(f'❌ Сталась помилка зверніться до адміністратора {e}.')
    except Exception as e:
        logger.error(f'При внесені домашнього завдання до бази даних відбулась помилка {e}.')
        await message.answer('❌ Відбулась помилка при внесенні до бази даних.')
        await state.clear()