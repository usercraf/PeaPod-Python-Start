import asyncio
from aiogram.filters.command import Command

from aiogram import Bot, Dispatcher, types, F
from aiogram.exceptions import TelegramNetworkError


from key_file import TOKEN
from log_file import logger

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_bot(message: types.Message):
    await message.answer(f'Вітаю тебе {message.from_user.first_name}!')


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