import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from config import config
from handlers.main_handler import router


async def start_bot():
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher(bot=bot)
    dp.include_router(router=router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(start_bot())