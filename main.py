import asyncio

from aiogram.filters.command import Command

from aiogram import Bot, Dispatcher, types, F
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from key_file import TOKEN, buttons_students, button_admin
from log_file import logger
from db_file import base
from student_file import students_router
from admin_file import admin_router

bot = Bot(token=TOKEN)
dp = Dispatcher()

def clear_unread_results(cur):
    try:
        while cur.nextset():
            pass
    except:
        pass

async def send_main_menu(user_id: int, user_name: str, send_func):
    try:
        if not base.is_connected():
            base.reconnect()

        with base.cursor() as cur:
            try:
                while cur.nextset():  # очищення залишків
                    pass
            except Exception:
                pass

            cur.execute("SELECT role, verification FROM students WHERE tg_id=%s", (user_id,))
            data = cur.fetchone()

        builder = InlineKeyboardBuilder()

        if data is None:
            builder.add(types.InlineKeyboardButton(text='⬇️ Тут', callback_data='verification'))
            await send_func("🤷🏼‍♂️ Ви відсутні в базі. Зверніться до адміністратора або верифікуйся.",
                            reply_markup=builder.as_markup())
            return

        role, verification = data

        if role == 'ADMIN':
            for key, value in button_admin().items():
                builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
            builder.adjust(1)
            await send_func(f'💪 Вітаю адміністраторе {user_name}, що будемо робити?',
                            reply_markup=builder.as_markup())

        elif role == 'student' and verification == 1:
            for key, value in buttons_students().items():
                builder.add(types.InlineKeyboardButton(text=value, callback_data=key))
            builder.adjust(1)
            await send_func(f'🐍 Вітаю тебе {user_name}, що будемо робити?',
                            reply_markup=builder.as_markup())

        else:
            builder.add(types.InlineKeyboardButton(text='⬇️ Тут', callback_data='verification'))
            await send_func('🔐 Верифікуйся', reply_markup=builder.as_markup())

    except Exception as e:
            logger.exception(f"💥 Помилка в send_main_menu: {e}")
            await send_func("⚠️ Сталась помилка. Спробуйте пізніше.")


@dp.message(Command("start"))
async def start_bot(message: types.Message):
    try:
        await send_main_menu(
            user_id=message.from_user.id,
            user_name=message.from_user.first_name,
            send_func=message.answer
        )
    except TelegramBadRequest as e:
        logger.error(f'❌ BadRequest: {e}')
        await message.answer('❌ Сталась помилка. Спробуйте пізніше.')
    except TelegramForbiddenError as e:
        logger.error(f'⛔️ Forbidden: {e}')
        await message.answer('⛔️ Ви заблокували бота або видалили чат.')


@dp.callback_query(F.data == 'Home')
async def home(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()
        await send_main_menu(
            user_id=callback.from_user.id,
            user_name=callback.from_user.first_name,
            send_func=callback.message.answer
        )
    except Exception as e:
        await state.clear()
        logger.error(f'❌ Помилка при натисканні "На головну": {e}')
        await callback.message.answer('❌ Сталась помилка. Зверніться до адміністратора.')



async def main():
    dp.include_router(students_router)
    dp.include_router(admin_router)
    tryings = 0
    # while True:
    try:
        print("🚀 Bot run")
        logger.info('Бот стартує.')
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