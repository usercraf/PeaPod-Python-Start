import asyncio

from aiogram.filters.command import Command

from aiogram import Bot, Dispatcher, types, F
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from key_file import TOKEN, buttons_students, button_admin
from log_file import logger
from db_file import cur
from student_file import students_router
from admin_file import admin_router

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_bot(message: types.Message):
    try:
        data = cur.execute("""SELECT role, verification FROM students WHERE tg_id=?""", (message.from_user.id,)).fetchone()
        builder = InlineKeyboardBuilder()

        if data is None:
            await message.answer('🤷🏼‍♂️ Ви відсутні в базі даних.\nЗверніться до адміністратора або верифікуйся.')
            builder.add(types.InlineKeyboardButton(text='⬇️ Тут', callback_data='verification'))
            await message.answer('Верифікуйся', reply_markup=builder.as_markup())
            return

        role, verification = data
        if role == 'ADMIN':
            for key, value in button_admin().items():
                builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
            builder.adjust(1)
            await message.answer(f'💪 Вітаю адміністраторе {message.from_user.first_name}, що будемо робити?',
                                 reply_markup=builder.as_markup())
        elif role == 'student' and verification == 1:
            for key, value in buttons_students().items():
                builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
            builder.adjust(1)
            await message.answer(f'🐍 Вітаю тебе {message.from_user.first_name}, що будемо робити?',
                                 reply_markup=builder.as_markup())
        else:
            builder.add(types.InlineKeyboardButton(text='⬇️ Тут', callback_data='verification'))
            await message.answer('Верифікуйся', reply_markup=builder.as_markup())
    except TelegramBadRequest as e:
        logger.error(f'Користувач {message.from_user.id} видалив чат або бот не має дозволу писати {e}.')
        await message.answer(f'❌ Сталась помилка зверніться до адміністратора {e}.')
    except TelegramForbiddenError as e:
        logger.error(f'Користувач {message.from_user.id} заблокував бота {e}')
        await message.answer(f'❌ Сталась помилка зверніться до адміністратора {e}.')


@dp.callback_query(F.data == 'Home')
async def home(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        data = cur.execute("""SELECT role, verification FROM students WHERE tg_id=?""", (callback.from_user.id,)).fetchone()
        builder = InlineKeyboardBuilder()
        role, verification = data
        if role == 'ADMIN':
            for key, value in button_admin().items():
                builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
            builder.adjust(1)
            await callback.message.answer(f'💪 Вітаю адміністраторе {callback.from_user.first_name}, що будемо робити?',
                                 reply_markup=builder.as_markup())
        elif role == 'student' and verification == 1:
            for key, value in buttons_students().items():
                builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
            builder.adjust(1)
            await callback.message.answer(f'🐍 Вітаю тебе {callback.from_user.first_name}, що будемо робити?',
                                 reply_markup=builder.as_markup())
    except Exception as e:
        await state.clear()
        logger.error(f'Помилка при натисканні кнопки НА ГОЛОВНУ {e}')
        await callback.message.answer(f'❌ Сталась помилка зверніться до адміністратора {e}.')



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