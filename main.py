import asyncio
import logging
import os

from aiohttp import web

from bot.config import settings
from bot.db import init_db, close_db
from bot.ai import close_ai_client
from bot.utils import setup_logging
from bot.handlers import router
from bot.middlewares import DBSessionMiddleware, LoggingMiddleware

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

setup_logging()
logger = logging.getLogger(__name__)


async def health_check(request):
    return web.Response(text="OK")


async def start_health_server():
    app = web.Application()
    app.router.add_get("/health", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Health check server started on port {port}")
    return runner


async def main() -> None:
    logger.info("Starting bot...")

    await init_db()
    logger.info("Database initialized")

    health_runner = await start_health_server()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.update.middleware(DBSessionMiddleware())
    dp.update.middleware(LoggingMiddleware())
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await health_runner.cleanup()
        await bot.session.close()
        await close_db()
        await close_ai_client()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")