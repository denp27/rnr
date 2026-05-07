from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Купить звёзды ⭐", callback_data="buy_stars")],
        [InlineKeyboardButton(text="💎 Купить Premium 💎", callback_data="buy_premium")],
        [InlineKeyboardButton(text="🎁 Купить подарок 🎁", callback_data="buy_gift")],
        [InlineKeyboardButton(text="💰 Профиль 💰", callback_data="profile")],
        [InlineKeyboardButton(text="📡 Звёзды канала 📡", callback_data="channel_stars")],
        [InlineKeyboardButton(text="📊 Подарки Telegram 🎨", callback_data="list_gifts")],
        [InlineKeyboardButton(text="❓ FAQ ❓", callback_data="faq_menu")]
    ])

def profile_keyboard(has_promo=False):
    buttons = [
        [InlineKeyboardButton(text="🏦 Пополнить баланс 💳", callback_data="topup")],
        [InlineKeyboardButton(text="🎫 Ввести промокод 🎁", callback_data="enter_promo")],
    ]
    if has_promo:
        buttons.insert(1, [InlineKeyboardButton(text="✨ Активная скидка ✨", callback_data="show_promo")])
    buttons.append([InlineKeyboardButton(text="🔙 Главное меню 🔙", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def payment_methods_keyboard(amount):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏦 СБП (Platega) 🇷🇺", callback_data=f"pay_platega_{amount}")],
        [InlineKeyboardButton(text="💎 Aurura Pay 🌟", callback_data=f"pay_aurura_{amount}")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="profile")]
    ])

def stars_target_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Себе 👤", callback_data="stars_self")],
        [InlineKeyboardButton(text="👥 Другому 👥", callback_data="stars_other")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="main_menu")]
    ])

def stars_amount_keyboard():
    amounts = [50, 100, 150, 250, 350, 500, 750, 1000, 1500, 2500, 5000, 10000, 25000]
    buttons = []
    for i in range(0, len(amounts), 2):
        row = []
        row.append(InlineKeyboardButton(text=f"{amounts[i]} ⭐", callback_data=f"stars_{amounts[i]}"))
        if i+1 < len(amounts):
            row.append(InlineKeyboardButton(text=f"{amounts[i+1]} ⭐", callback_data=f"stars_{amounts[i+1]}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="buy_stars")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def premium_target_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Себе 👤", callback_data="prem_self")],
        [InlineKeyboardButton(text="👥 Другому 👥", callback_data="prem_other")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="main_menu")]
    ])

def premium_duration_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 3 месяца — 1165 ₽", callback_data="prem_3")],
        [InlineKeyboardButton(text="📅 6 месяцев — 1555 ₽", callback_data="prem_6")],
        [InlineKeyboardButton(text="📅 12 месяцев — 2819 ₽", callback_data="prem_12")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="buy_premium")]
    ])

def gift_target_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Себе 👤", callback_data="gift_self")],
        [InlineKeyboardButton(text="👥 Другому 👥", callback_data="gift_other")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="main_menu")]
    ])

def gift_comment_final_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Добавить комментарий ✏️", callback_data="add_comment_text")],
        [InlineKeyboardButton(text="📤 Отправить без комментария 📤", callback_data="send_without_comment")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="back_to_gift_selection")]
    ])

def gift_comment_with_text_keyboard(comment_preview):
    preview = comment_preview[:30] + "..." if len(comment_preview) > 30 else comment_preview
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💬 {preview}", callback_data="noop")],
        [InlineKeyboardButton(text="✅ Отправить с комментарием ✅", callback_data="send_with_comment")],
        [InlineKeyboardButton(text="✏️ Изменить комментарий ✏️", callback_data="edit_comment_text")],
        [InlineKeyboardButton(text="🗑 Удалить комментарий 🗑", callback_data="remove_comment")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="back_to_comment_menu")]
    ])

def channel_stars_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Баланс канала 📊", callback_data="channel_balance")],
        [InlineKeyboardButton(text="📈 Статистика 📈", callback_data="channel_stats")],
        [InlineKeyboardButton(text="💸 Вывести звёзды 💸", callback_data="channel_withdraw")],
        [InlineKeyboardButton(text="📋 История транзакций 📋", callback_data="channel_history")],
        [InlineKeyboardButton(text="🔄 Обновить баланс 🔄", callback_data="channel_refresh")],
        [InlineKeyboardButton(text="❓ Помощь по выводу ❓", callback_data="channel_withdraw_help")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="main_menu")]
    ])

def channel_balance_actions_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💸 Вывести звёзды 💸", callback_data="channel_withdraw")],
        [InlineKeyboardButton(text="📈 Статистика 📈", callback_data="channel_stats")],
        [InlineKeyboardButton(text="🔄 Другой канал 🔄", callback_data="channel_balance")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="channel_stars_back")]
    ])

def faq_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❓ Как купить звёзды? ❓", callback_data="faq_buy_stars")],
        [InlineKeyboardButton(text="💎 Как купить Premium? 💎", callback_data="faq_buy_premium")],
        [InlineKeyboardButton(text="🎁 Как подарить подарок? 🎁", callback_data="faq_send_gift")],
        [InlineKeyboardButton(text="💰 Как пополнить баланс? 💰", callback_data="faq_topup")],
        [InlineKeyboardButton(text="👥 Реферальная программа 👥", callback_data="faq_referral")],
        [InlineKeyboardButton(text="🆘 Поддержка 24/7 🆘", callback_data="faq_support")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="main_menu")]
    ])

def faq_answer_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К вопросам 🔙", callback_data="faq_back")],
        [InlineKeyboardButton(text="🆘 Связаться с поддержкой 🆘", callback_data="faq_support_contact")],
        [InlineKeyboardButton(text="🔙 В главное меню 🔙", callback_data="main_menu")]
    ])

def admin_main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Пользователи 👥", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 Статистика 📊", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🎫 Промокоды 🎫", callback_data="admin_promos")],
        [InlineKeyboardButton(text="📨 Рассылка 📨", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="🏆 Топ пользователей 🏆", callback_data="admin_top")],
        [InlineKeyboardButton(text="⚙️ Настройки ⚙️", callback_data="admin_settings")],
        [InlineKeyboardButton(text="🔙 Главное меню 🔙", callback_data="main_menu")]
    ])

def admin_users_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск пользователя 🔍", callback_data="admin_find_user")],
        [InlineKeyboardButton(text="➕ Выдать баланс ➕", callback_data="admin_add_balance")],
        [InlineKeyboardButton(text="➖ Списать баланс ➖", callback_data="admin_remove_balance")],
        [InlineKeyboardButton(text="👑 Назначить админа 👑", callback_data="admin_make_admin")],
        [InlineKeyboardButton(text="📋 Список админов 📋", callback_data="admin_list_admins")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="admin_panel")]
    ])

def admin_promos_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать промокод ➕", callback_data="admin_create_promo")],
        [InlineKeyboardButton(text="📋 Список промокодов 📋", callback_data="admin_list_promos")],
        [InlineKeyboardButton(text="🗑 Удалить промокод 🗑", callback_data="admin_delete_promo")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="admin_panel")]
    ])

def admin_broadcast_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Текст 📝", callback_data="broadcast_text")],
        [InlineKeyboardButton(text="🖼 Фото 🖼", callback_data="broadcast_photo")],
        [InlineKeyboardButton(text="🎥 Видео 🎥", callback_data="broadcast_video")],
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="admin_panel")]
    ])

def admin_broadcast_confirm_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, отправить ✅", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отмена ❌", callback_data="admin_panel")]
    ])

def back_button(callback_data="main_menu"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data=callback_data)]
    ])

def error_keyboard(back_callback="main_menu"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Попробовать снова 🔄", callback_data=back_callback)],
        [InlineKeyboardButton(text="🔙 Главное меню 🔙", callback_data="main_menu")]
    ])

def payment_success_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Профиль 💰", callback_data="profile")],
        [InlineKeyboardButton(text="⭐ Купить звёзды ⭐", callback_data="buy_stars")],
        [InlineKeyboardButton(text="🔙 В меню 🔙", callback_data="main_menu")]
    ])

def withdrawal_success_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Профиль 💰", callback_data="profile")],
        [InlineKeyboardButton(text="⭐ Купить звёзды ⭐", callback_data="buy_stars")],
        [InlineKeyboardButton(text="🔙 В меню 🔙", callback_data="main_menu")]
    ])