import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", 0))
    TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
    FRAGMENT_API_KEY = os.getenv("FRAGMENT_API_KEY")
    FRAGMENT_SEED = os.getenv("FRAGMENT_SEED")
    PLATEGA_API_KEY = os.getenv("PLATEGA_API_KEY")
    PLATEGA_SHOP_ID = os.getenv("PLATEGA_SHOP_ID")
    PLATEGA_SECRET = os.getenv("PLATEGA_SECRET")
    AURURA_API_KEY = os.getenv("AURURA_API_KEY")
    AURURA_SECRET_KEY = os.getenv("AURURA_SECRET_KEY")
    AURURA_WALLET_ID = os.getenv("AURURA_WALLET_ID")
    AURURA_CALLBACK_SECRET = os.getenv("AURURA_CALLBACK_SECRET")
    WEBHOOK_URL = os.getenv("WEBHOOK_URL")
    WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", 8000))
    SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "support")
    RUB_PER_STAR = 1.46
    MIN_WITHDRAW_STARS = 100
    MAX_WITHDRAW_STARS = 1000000
    MIN_TOPUP_RUB = 10
    MAX_TOPUP_RUB = 100000
    MAX_COMMENT_LENGTH = 255
