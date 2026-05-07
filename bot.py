import asyncio
import logging
import sys
from logging.handlers import RotatingFileHandler
from threading import Thread

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import init_db
from handlers import start, profile, buy_stars, buy_premium, buy_gift, channel_stars, faq, admin

def setup_logging():
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler = RotatingFileHandler('bot.log', maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO)
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(file_handler)
    root.addHandler(console_handler)
    logging.getLogger('aiogram').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.info("Логирование настроено")

setup_logging()
logger = logging.getLogger(__name__)

bot = Bot(token=Config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

dp.include_router(start.router)
dp.include_router(profile.router)
dp.include_router(buy_stars.router)
dp.include_router(buy_premium.router)
dp.include_router(buy_gift.router)
dp.include_router(channel_stars.router)
dp.include_router(faq.router)
dp.include_router(admin.router)

def run_webhook():
    import uvicorn
    from webhook.server import app
    logger.info(f"Запуск вебхук сервера на порту {Config.WEBHOOK_PORT}")
    uvicorn.run(app, host="0.0.0.0", port=Config.WEBHOOK_PORT)

async def main():
    init_db()
    logger.info("База данных инициализирована")
    thread = Thread(target=run_webhook, daemon=True)
    thread.start()
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
