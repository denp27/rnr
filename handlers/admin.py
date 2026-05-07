import asyncio
import logging
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from database import Session, User, Transaction, Admin, get_user, update_balance, add_transaction, is_admin
from services.promo_manager import PromoCodeManager
from keyboards.all_keyboards import (
    admin_main_keyboard, admin_users_keyboard, admin_promos_keyboard,
    admin_broadcast_type_keyboard, admin_broadcast_confirm_keyboard,
    back_button
)

router = Router()
logger = logging.getLogger(__name__)
promo_manager = PromoCodeManager()

class AdminStates(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_balance_amount = State()
    waiting_for_new_admin_id = State()
    waiting_for_promo_code = State()
    waiting_for_promo_discount = State()
    waiting_for_promo_uses = State()
    waiting_for_promo_min_payment = State()
    waiting_for_promo_expiry = State()
    waiting_for_promo_description = State()
    waiting_for_search_query = State()
    waiting_for_broadcast_text = State()
    waiting_for_broadcast_photo = State()
    waiting_for_broadcast_video = State()
    waiting_for_broadcast_buttons = State()

@router.callback_query(lambda c: c.data == "admin_panel")
async def admin_panel(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён", show_alert=True)
        return
    await callback.message.edit_text("🛡️ **Админ-панель**", reply_markup=admin_main_keyboard())
    await state.clear()

@router.callback_query(lambda c: c.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    await callback.message.edit_text("👥 Управление пользователями", reply_markup=admin_users_keyboard())

@router.callback_query(lambda c: c.data == "admin_find_user")
async def admin_find_user(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🔍 Введите ID или username:", reply_markup=back_button("admin_users"))
    await state.set_state(AdminStates.waiting_for_search_query)

@router.message(AdminStates.waiting_for_search_query)
async def process_search_user(message: types.Message, state: FSMContext):
    query = message.text.strip()
    session = Session()
    if query.isdigit():
        user = session.query(User).filter_by(telegram_id=int(query)).first()
    else:
        user = session.query(User).filter(User.username.ilike(f"%{query}%")).first()
    if not user:
        await message.answer("❌ Не найден", reply_markup=back_button("admin_users"))
        return
    refs = session.query(User).filter_by(referrer_id=user.telegram_id).count()
    await message.answer(f"👤 ID: {user.telegram_id}\n@{user.username}\n💰 {user.balance:.2f} ₽\n👥 Рефералов: {refs}")
    await state.clear()

@router.callback_query(lambda c: c.data in ["admin_add_balance", "admin_remove_balance"])
async def admin_balance_start(callback: CallbackQuery, state: FSMContext):
    action = "add" if callback.data == "admin_add_balance" else "remove"
    await state.update_data(remove_mode=(action=="remove"))
    await callback.message.edit_text("Введите Telegram ID пользователя:", reply_markup=back_button("admin_users"))
    await state.set_state(AdminStates.waiting_for_user_id)

@router.message(AdminStates.waiting_for_user_id)
async def admin_get_user_id(message: types.Message, state: FSMContext):
    try:
        uid = int(message.text)
        user = get_user(uid)
        if not user:
            await message.answer("❌ Не найден")
            return
        await state.update_data(target_id=uid)
        await message.answer(f"👤 @{user.username}\n💰 {user.balance:.2f} ₽\n\nВведите сумму:")
        await state.set_state(AdminStates.waiting_for_balance_amount)
    except:
        await message.answer("❌ Введите ID числом")

@router.message(AdminStates.waiting_for_balance_amount)
async def admin_process_balance(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        data = await state.get_data()
        uid = data["target_id"]
        remove = data.get("remove_mode", False)
        user = get_user(uid)
        if remove and user.balance < amount:
            await message.answer(f"❌ Недостаточно. Баланс: {user.balance:.2f} ₽")
            return
        final = -amount if remove else amount
        update_balance(uid, final)
        add_transaction(uid, "admin_credit" if not remove else "admin_debit", final)
        await message.bot.send_message(uid, f"{'✅ Начислено' if not remove else '⚠️ Списано'} {amount:.2f} ₽")
        await message.answer(f"✅ Готово. Новый баланс @{user.username}: {user.balance + final:.2f} ₽")
        await state.clear()
    except:
        await message.answer("❌ Введите число")

@router.callback_query(lambda c: c.data == "admin_make_admin")
async def admin_make_admin_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👑 Введите Telegram ID:", reply_markup=back_button("admin_users"))
    await state.set_state(AdminStates.waiting_for_new_admin_id)

@router.message(AdminStates.waiting_for_new_admin_id)
async def admin_make_admin(message: types.Message, state: FSMContext):
    try:
        aid = int(message.text)
        session = Session()
        if session.query(Admin).filter_by(telegram_id=aid).first():
            await message.answer("❌ Уже админ")
        else:
            admin = Admin(telegram_id=aid, added_by=message.from_user.id)
            session.add(admin)
            session.commit()
            await message.answer(f"✅ Админ {aid} назначен")
        session.close()
        await state.clear()
    except:
        await message.answer("❌ Ошибка")

@router.callback_query(lambda c: c.data == "admin_list_admins")
async def admin_list_admins(callback: CallbackQuery):
    session = Session()
    admins = session.query(Admin).filter_by(is_active=True).all()
    text = "👑 **Админы:**\n" + "\n".join([f"🆔 {a.telegram_id}" for a in admins]) if admins else "Нет"
    await callback.message.edit_text(text, reply_markup=back_button("admin_users"))
    session.close()

@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    session = Session()
    total_users = session.query(User).count()
    stars_tx = session.query(Transaction).filter_by(type="stars").count()
    revenue = session.query(Transaction).filter(Transaction.type.in_(["topup","channel_withdraw"])).with_entities(func.sum(Transaction.amount)).scalar() or 0
    await callback.message.edit_text(f"📊 **Статистика**\n👥 {total_users}\n⭐ {stars_tx} покупок звёзд\n💰 {revenue:.2f} ₽", reply_markup=back_button("admin_panel"))
    session.close()

@router.callback_query(lambda c: c.data == "admin_top")
async def admin_top(callback: CallbackQuery):
    session = Session()
    top_bal = session.query(User).order_by(User.balance.desc()).limit(10).all()
    top_ref = session.query(User).order_by(User.referrals_count.desc()).limit(10).all()
    text = "🏆 **Топ по балансу**\n" + "\n".join([f"{i+1}. @{u.username} — {u.balance:.2f} ₽" for i,u in enumerate(top_bal)])
    text += "\n\n🏆 **Топ по рефералам**\n" + "\n".join([f"{i+1}. @{u.username} — {u.referrals_count}" for i,u in enumerate(top_ref)])
    await callback.message.edit_text(text, reply_markup=back_button("admin_panel"))
    session.close()

@router.callback_query(lambda c: c.data == "admin_promos")
async def admin_promos(callback: CallbackQuery):
    await callback.message.edit_text("🎫 Промокоды", reply_markup=admin_promos_keyboard())

@router.callback_query(lambda c: c.data == "admin_create_promo")
async def admin_create_promo_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("➕ Введите код (или `auto`):", reply_markup=back_button("admin_promos"))
    await state.set_state(AdminStates.waiting_for_promo_code)

@router.message(AdminStates.waiting_for_promo_code)
async def admin_promo_code(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(promo_code=code if code != "AUTO" else None)
    await message.answer("Введите скидку %:")
    await state.set_state(AdminStates.waiting_for_promo_discount)

@router.message(AdminStates.waiting_for_promo_discount)
async def admin_promo_discount(message: types.Message, state: FSMContext):
    try:
        disc = int(message.text)
        await state.update_data(discount=disc)
        await message.answer("Макс. использований (1):")
        await state.set_state(AdminStates.waiting_for_promo_uses)
    except:
        await message.answer("❌ Число")

@router.message(AdminStates.waiting_for_promo_uses)
async def admin_promo_uses(message: types.Message, state: FSMContext):
    uses = int(message.text) if message.text.isdigit() else 1
    await state.update_data(max_uses=uses)
    await message.answer("Мин. сумма (0):")
    await state.set_state(AdminStates.waiting_for_promo_min_payment)

@router.message(AdminStates.waiting_for_promo_min_payment)
async def admin_promo_min_payment(message: types.Message, state: FSMContext):
    try:
        minp = float(message.text.replace(",", "."))
    except:
        minp = 0
    await state.update_data(min_payment=minp)
    await message.answer("Срок (дней, 30):")
    await state.set_state(AdminStates.waiting_for_promo_expiry)

@router.message(AdminStates.waiting_for_promo_expiry)
async def admin_promo_expiry(message: types.Message, state: FSMContext):
    days = int(message.text) if message.text.isdigit() else 30
    await state.update_data(expires_days=days)
    await message.answer("Описание (или `-`):")
    await state.set_state(AdminStates.waiting_for_promo_description)

@router.message(AdminStates.waiting_for_promo_description)
async def admin_promo_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    desc = None if message.text == "-" else message.text
    result = promo_manager.create_promo(
        created_by=message.from_user.id,
        discount_percent=data["discount"],
        max_uses=data["max_uses"],
        min_payment=data["min_payment"],
        expires_days=data["expires_days"],
        custom_code=data.get("promo_code"),
        description=desc
    )
    if result["success"]:
        await message.answer(f"✅ Промокод `{result['code']}` создан\nСкидка {result['discount_percent']}%")
    else:
        await message.answer(f"❌ {result['error']}")
    await state.clear()

@router.callback_query(lambda c: c.data == "admin_list_promos")
async def admin_list_promos(callback: CallbackQuery):
    promos = promo_manager.get_all_promos()
    if not promos:
        await callback.message.edit_text("Нет промокодов", reply_markup=back_button("admin_promos"))
        return
    text = "📋 Промокоды:\n" + "\n".join([f"`{p['code']}` — {p['discount_percent']}% (исп. {p['used_count']}/{p['max_uses']})" for p in promos])
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=back_button("admin_promos"))

@router.callback_query(lambda c: c.data == "admin_delete_promo")
async def admin_delete_promo_start(callback: CallbackQuery):
    promos = promo_manager.get_all_promos()
    if not promos:
        await callback.answer("Нет промокодов")
        return
    buttons = [[InlineKeyboardButton(text=p['code'], callback_data=f"delpromo_{p['id']}")] for p in promos]
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_promos")])
    await callback.message.edit_text("Выберите для удаления:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(lambda c: c.data.startswith("delpromo_"))
async def admin_delete_promo(callback: CallbackQuery):
    pid = int(callback.data.split("_")[1])
    if promo_manager.delete_promo(pid):
        await callback.answer("✅ Удалён")
    else:
        await callback.answer("❌ Ошибка")
    await admin_promos(callback)

@router.callback_query(lambda c: c.data == "admin_broadcast")
async def admin_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📨 Выберите тип рассылки:", reply_markup=admin_broadcast_type_keyboard())
    await state.set_state(AdminStates.waiting_for_broadcast_text)  # временно

@router.callback_query(lambda c: c.data.startswith("broadcast_"))
async def broadcast_type(callback: CallbackQuery, state: FSMContext):
    btype = callback.data.split("_")[1]
    await state.update_data(broadcast_type=btype)
    if btype == "text":
        await callback.message.edit_text("📝 Введите текст:", reply_markup=back_button("admin_panel"))
        await state.set_state(AdminStates.waiting_for_broadcast_text)
    elif btype == "photo":
        await callback.message.edit_text("🖼 Отправьте фото:", reply_markup=back_button("admin_panel"))
        await state.set_state(AdminStates.waiting_for_broadcast_photo)
    elif btype == "video":
        await callback.message.edit_text("🎥 Отправьте видео:", reply_markup=back_button("admin_panel"))
        await state.set_state(AdminStates.waiting_for_broadcast_video)

@router.message(AdminStates.waiting_for_broadcast_photo, F.photo)
async def broadcast_photo(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    caption = message.caption or ""
    await state.update_data(media_id=file_id, broadcast_text=caption)
    await message.answer("✅ Фото получено. Теперь введите кнопки (формат `текст - url; ...`) или `-` :")
    await state.set_state(AdminStates.waiting_for_broadcast_buttons)

@router.message(AdminStates.waiting_for_broadcast_video, F.video)
async def broadcast_video(message: types.Message, state: FSMContext):
    file_id = message.video.file_id
    caption = message.caption or ""
    await state.update_data(media_id=file_id, broadcast_text=caption)
    await message.answer("✅ Видео получено. Введите кнопки или `-`:")
    await state.set_state(AdminStates.waiting_for_broadcast_buttons)

@router.message(AdminStates.waiting_for_broadcast_text)
async def broadcast_text(message: types.Message, state: FSMContext):
    text = message.text
    await state.update_data(broadcast_text=text)
    await message.answer("📝 Текст получен. Введите кнопки или `-`:")
    await state.set_state(AdminStates.waiting_for_broadcast_buttons)

@router.message(AdminStates.waiting_for_broadcast_buttons)
async def broadcast_buttons(message: types.Message, state: FSMContext):
    data = await state.get_data()
    btype = data.get("broadcast_type")
    text = data.get("broadcast_text")
    raw_buttons = message.text.strip()
    keyboard = None
    if raw_buttons != "-" and " - " in raw_buttons:
        btns = []
        for part in raw_buttons.split(";"):
            if " - " in part:
                btn_txt, url = part.split(" - ", 1)
                btns.append([InlineKeyboardButton(text=btn_txt.strip(), url=url.strip())])
        if btns:
            keyboard = InlineKeyboardMarkup(inline_keyboard=btns)
    await state.update_data(broadcast_keyboard=keyboard)
    # предпросмотр
    if btype == "photo":
        await message.answer_photo(data["media_id"], caption=text, reply_markup=keyboard)
    elif btype == "video":
        await message.answer_video(data["media_id"], caption=text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)
    await message.answer("Отправить рассылку?", reply_markup=admin_broadcast_confirm_keyboard())
    await state.set_state(AdminStates.waiting_for_broadcast_buttons)  # фиктивное

@router.callback_query(lambda c: c.data == "broadcast_confirm")
async def broadcast_send(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    btype = data.get("broadcast_type")
    text = data.get("broadcast_text")
    keyboard = data.get("broadcast_keyboard")
    media = data.get("media_id")
    session = Session()
    users = session.query(User).all()
    session.close()
    success = 0
    for user in users:
        try:
            if btype == "photo":
                await callback.bot.send_photo(user.telegram_id, media, caption=text, reply_markup=keyboard)
            elif btype == "video":
                await callback.bot.send_video(user.telegram_id, media, caption=text, reply_markup=keyboard)
            else:
                await callback.bot.send_message(user.telegram_id, text, reply_markup=keyboard)
            success += 1
        except:
            pass
        await asyncio.sleep(0.05)
    await callback.message.edit_text(f"✅ Рассылка завершена\nОтправлено: {success}")
    await state.clear()

@router.callback_query(lambda c: c.data == "admin_settings")
async def admin_settings(callback: CallbackQuery):
    await callback.message.edit_text("⚙️ Настройки в разработке", reply_markup=back_button("admin_panel"))
