import logging
import os
from aiogram import Bot, Dispatcher
from handlers import router
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(router)


async def main():
    logger.info("Бот запускается...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")


if __name__ == "__main__":
    asyncio.run(main())

