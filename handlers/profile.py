import logging
from datetime import datetime, timedelta
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from config import Config
from database import get_user, update_balance, add_transaction, Session, User
from services.promo_manager import PromoCodeManager
from services.platega_client import PlategaClient
from services.aurura_pay import AururaPaymentHandler
from keyboards.all_keyboards import profile_keyboard, payment_methods_keyboard, back_button, error_keyboard

router = Router()
logger = logging.getLogger(__name__)
promo_manager = PromoCodeManager()
platega_client = PlategaClient()
aurura_handler = AururaPaymentHandler(None)

class ProfileStates(StatesGroup):
    entering_promo = State()
    entering_topup_amount = State()
    choosing_payment_method = State()

@router.callback_query(lambda c: c.data == "profile")
async def show_profile(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    session = Session()
    referrals_count = session.query(User).filter_by(referrer_id=user.telegram_id).count()
    session.close()
    has_promo = user.promo_discount > 0 and user.promo_expires and user.promo_expires > datetime.now()
    bot_username = (await callback.bot.get_me()).username
    ref_link = f"https://t.me/{bot_username}?start=ref{user.telegram_id}"
    text = (
        f"📊 **Профиль** 📊\n\n"
        f"💰 **Баланс:** {user.balance:.2f} ₽\n"
        f"⭐ **Куплено звёзд:** {user.total_stars_bought} 🌟\n"
        f"🆔 **ID:** {user.id}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **Реферальная программа** 👥\n"
        f"└ Рефералов: {referrals_count}\n"
        f"└ Процент: 10% от прибыли 🔥\n\n"
        f"🔗 **Ваша ссылка:**\n`{ref_link}`\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 **Промокод** 🎫\n"
        f"└ Введите промокод для получения скидки 💸\n"
    )
    if has_promo:
        text += f"\n✨ **Ваша активная скидка:** {user.promo_discount}% ✨"
    await callback.message.edit_text(text, reply_markup=profile_keyboard(has_promo), parse_mode="Markdown")

@router.callback_query(lambda c: c.data == "topup")
async def start_topup(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    promo_text = ""
    if user.promo_discount > 0 and user.promo_expires and user.promo_expires > datetime.now():
        promo_text = f"\n\n✨ Ваша скидка: {user.promo_discount}% ✨"
    await callback.message.edit_text(
        f"💰 **Пополнение баланса** 💰\n\n"
        f"Введите сумму в рублях:\n"
        f"• Минимум: {Config.MIN_TOPUP_RUB} ₽\n"
        f"• Максимум: {Config.MAX_TOPUP_RUB} ₽{promo_text}\n\n"
        f"Пример: `100` или `500.50`",
        parse_mode="Markdown",
        reply_markup=back_button("profile")
    )
    await state.set_state(ProfileStates.entering_topup_amount)

@router.message(ProfileStates.entering_topup_amount)
async def process_topup_amount(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", "."))
        if amount < Config.MIN_TOPUP_RUB or amount > Config.MAX_TOPUP_RUB:
            await message.answer(f"❌ Сумма должна быть от {Config.MIN_TOPUP_RUB} до {Config.MAX_TOPUP_RUB} ₽")
            return
        user = get_user(message.from_user.id)
        if user.promo_discount > 0 and user.promo_expires and user.promo_expires > datetime.now():
            discount = amount * (user.promo_discount / 100)
            amount = amount - discount
            await message.answer(f"✨ Применена скидка {user.promo_discount}%! Сумма к оплате: {amount:.2f} ₽")
        await state.update_data(topup_amount=amount)
        await message.answer("Выберите способ оплаты:", reply_markup=payment_methods_keyboard(amount))
        await state.set_state(ProfileStates.choosing_payment_method)
    except ValueError:
        await message.answer("❌ Введите корректную сумму")

@router.callback_query(lambda c: c.data.startswith("pay_platega_"), ProfileStates.choosing_payment_method)
async def pay_platega(callback: CallbackQuery, state: FSMContext):
    amount = float(callback.data.split("_")[2])
    logger.info(f"Пользователь {callback.from_user.id} выбрал оплату Platega на сумму {amount}")
    await callback.message.edit_text("⏳ Создание платежа в Platega.io...")
    try:
        payment = await platega_client.create_payment(amount, f"ORDER_{callback.from_user.id}", callback.from_user.id)
        await callback.message.edit_text(
            f"🏦 **Оплата через СБП (Platega.io)** 🏦\n\n💰 {amount:.2f} ₽\n\n🔗 {payment['payment_url']}\n\n⏳ После оплаты баланс пополнится автоматически",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил ✅", callback_data=f"check_payment_{payment['payment_id']}")],
                [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="profile")]
            ])
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка Platega: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=error_keyboard("topup"))

@router.callback_query(lambda c: c.data.startswith("pay_aurura_"), ProfileStates.choosing_payment_method)
async def pay_aurura(callback: CallbackQuery, state: FSMContext):
    amount = float(callback.data.split("_")[2])
    logger.info(f"Пользователь {callback.from_user.id} выбрал оплату Aurura на сумму {amount}")
    await callback.message.edit_text("⏳ Создание платежа в Aurura Pay...")
    try:
        payment = await aurura_handler.init_payment(callback.from_user.id, amount)
        await callback.message.answer(
            f"💎 **Оплата через Aurura Pay** 💎\n\n💰 {amount:.2f} ₽\n\n🔗 {payment['payment_url']}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил ✅", callback_data=f"check_aurura_{payment['payment_id']}")],
                [InlineKeyboardButton(text="🔙 Назад 🔙", callback_data="profile")]
            ])
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка Aurura: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=error_keyboard("topup"))

@router.callback_query(lambda c: c.data == "enter_promo")
async def enter_promo(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎫 **Введите промокод**\n\nПример: `WELCOME10`\nСкидка будет применена к следующему пополнению.",
        parse_mode="Markdown",
        reply_markup=back_button("profile")
    )
    await state.set_state(ProfileStates.entering_promo)

@router.message(ProfileStates.entering_promo)
async def process_promo(message: types.Message, state: FSMContext):
    code = message.text.strip().upper()
    result = promo_manager.validate_code(code, message.from_user.id)
    if result["valid"]:
        session = Session()
        user = session.query(User).filter_by(telegram_id=message.from_user.id).first()
        if user:
            user.promo_discount = result["discount_percent"]
            user.promo_expires = datetime.now() + timedelta(days=30)
            session.commit()
        session.close()
        logger.info(f"Пользователь {message.from_user.id} активировал промокод {code} на {result['discount_percent']}%")
        await message.answer(f"✅ Промокод активирован! Скидка {result['discount_percent']}%", reply_markup=back_button("profile"))
    else:
        await message.answer(result["error"], reply_markup=error_keyboard("enter_promo"))
    await state.clear()
