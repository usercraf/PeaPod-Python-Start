import asyncio
import random
from aiogram.filters.command import Command

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramNetworkError
from aiogram.utils.keyboard import InlineKeyboardBuilder

from key_file import TOKEN
from log_file import logger
from db_file import cur, base

bot = Bot(token=TOKEN)
dp = Dispatcher()

def button_admin():
    return {
        'add_student':'🧑‍🎓 Додати студента',
        'del_student': '❌ Видалити студента',
        'add_stars': '🌟 Додати зірочки',
        'add_home_work': '📚 Додати домашнє завдання',
    }

def buttons_students():
    return {
        'home_work_students':'📚 Домашні завдання',
        'chek_start':'🌟 Перевірка зірочок',
    }

def generate_unique_code():
    while True:
        code = "{:06d}".format(random.randint(100000, 999999))
        exists = cur.execute("SELECT 1 FROM students WHERE code = ?", (code,)).fetchone()
        if not exists:
            return int(code)

@dp.message(Command("start"))
async def start_bot(message: types.Message):
    role = cur.execute("""SELECT role FROM students WHERE tg_id=?""", (message.from_user.id,)).fetchone()
    builder = InlineKeyboardBuilder()
    if role[0] == 'ADMIN':
        for key, value in button_admin().items():
            builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
        builder.adjust(1)
        await message.answer(f'Вітаю адміністраторе {message.from_user.first_name}, що будемо робити?',
                             reply_markup=builder.as_markup())
    elif role[0] == 'student':
        for key, value in buttons_students().items():
            builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
        builder.adjust(1)
        await message.answer(f'Вітаю тебе {message.from_user.first_name}, що будемо робити?',
                             reply_markup=builder.as_markup())
    else:
        builder.add(types.InlineKeyboardButton(text='Тут', callback_data='verification'))
        await message.answer('Верифікуйся', reply_markup=builder.as_markup())


async def main():
    tryings = 0
    while True:
        try:
            print("🚀 Bot run")
            await dp.start_polling(bot)
        except TelegramNetworkError as e:
            tryings += 1
            logger.warning(f"⚠️ TelegramNetworkError: {e}. Спроба №{tryings}")
            await asyncio.sleep(1.0 * tryings)
        except Exception as e:
            logger.exception(f"💥 Невідома помилка polling: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())