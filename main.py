import asyncio

from aiogram.filters.command import Command

from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramNetworkError
from aiogram.utils.keyboard import InlineKeyboardBuilder

from key_file import TOKEN, buttons_students, button_admin
from log_file import logger
from db_file import cur, base
from student_file import students_router
from admin_file import admin_router

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_bot(message: types.Message):
    data = cur.execute("""SELECT role, verification FROM students WHERE tg_id=?""", (message.from_user.id,)).fetchone()
    builder = InlineKeyboardBuilder()

    if data is None:
        await message.answer('Вас не знайдено в базі даних зверніться до адміністратора.')
        builder.add(types.InlineKeyboardButton(text='⬇️ Тут', callback_data='verification'))
        await message.answer('Верифікуйся', reply_markup=builder.as_markup())

    role, verification = data
    if role == 'ADMIN':
        for key, value in button_admin().items():
            builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
        builder.adjust(1)
        await message.answer(f'Вітаю адміністраторе {message.from_user.first_name}, що будемо робити?',
                             reply_markup=builder.as_markup())
    elif role == 'student' and verification == 1:
        for key, value in buttons_students().items():
            builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
        builder.adjust(1)
        await message.answer(f'Вітаю тебе {message.from_user.first_name}, що будемо робити?',
                             reply_markup=builder.as_markup())
    else:
        builder.add(types.InlineKeyboardButton(text='⬇️ Тут', callback_data='verification'))
        await message.answer('Верифікуйся', reply_markup=builder.as_markup())


async def main():
    dp.include_router(students_router)
    dp.include_router(admin_router)
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