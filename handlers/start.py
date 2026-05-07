import logging
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton

from database import get_user, Session, User
from handlers.admin import is_admin
from keyboards.all_keyboards import main_menu

router = Router()
logger = logging.getLogger(__name__)

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or str(user_id)
    logger.info(f"Пользователь {user_id} (@{username}) запустил бота")
    session = Session()
    user = session.query(User).filter_by(telegram_id=user_id).first()
    if not user:
        ref_id = None
        if len(message.text.split()) > 1 and message.text.split()[1].startswith("ref"):
            try:
                ref_id = int(message.text.split()[1][3:])
            except:
                pass
        user = User(telegram_id=user_id, username=username, referrer_id=ref_id)
        session.add(user)
        session.commit()
        if ref_id:
            referrer = session.query(User).filter_by(telegram_id=ref_id).first()
            if referrer:
                referrer.referrals_count += 1
                session.commit()
                logger.info(f"Реферал {user_id} пришел от {ref_id}")
    session.close()
    kb = main_menu()
    if is_admin(user_id):
        kb.inline_keyboard.append([InlineKeyboardButton(text="🛡️ Админ-панель 🛡️", callback_data="admin_panel")])
    await message.answer(
        "✨ **Приветствую в MstiStars!** ✨\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⭐ **Куплено звёзд через нас:** 153398\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**У нас вы можете:**\n"
        "🔵 Приобрести и подарить звёзды по низким ценам!\n"
        "🟠 Приобрести Telegram Premium\n"
        "✅ Купить TON на аккаунт\n"
        "📡 Вывести звёзды с телеграм канала\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "**Выберите действие ниже:**",
        reply_markup=kb,
        parse_mode="Markdown"
    )
