import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from config import BOT_TOKEN
from database import init_db
from handlers import admin, user

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL", "")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
WEB_PORT = int(os.getenv("PORT", 10000))


async def on_startup(bot: Bot):
    if WEBHOOK_HOST:
        await bot.set_webhook(WEBHOOK_URL)
        logging.info(f"Webhook set: {WEBHOOK_URL}")
    else:
        logging.info("No RENDER_EXTERNAL_URL — running in polling mode")


async def on_shutdown(bot: Bot):
    if WEBHOOK_HOST:
        await bot.delete_webhook()


async def polling_main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin.router)
    dp.include_router(user.router)
    logging.info("Bot polling rejimida ishga tushdi")
    await dp.start_polling(bot)


def webhook_main():
    init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(admin.router)
    dp.include_router(user.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=WEB_PORT)


if __name__ == "__main__":
    if WEBHOOK_HOST:
        webhook_main()
    else:
        asyncio.run(polling_main())
