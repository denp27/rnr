import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import get_user, update_balance, add_transaction
from services.fragment_client import FragmentClient
from keyboards.all_keyboards import premium_target_keyboard, premium_duration_keyboard, back_button, error_keyboard

router = Router()
fragment = FragmentClient()
logger = logging.getLogger(__name__)

class BuyPremiumStates(StatesGroup):
    choosing_target = State()
    entering_username = State()
    choosing_duration = State()

@router.callback_query(lambda c: c.data == "buy_premium")
async def buy_premium(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    logger.info(f"Пользователь {callback.from_user.id} начал покупку Premium")
    await callback.message.edit_text(
        f"💎 **Покупка Premium** 💎\n\n💰 Баланс: {user.balance:.2f} ₽\n\n👥 Кому?",
        reply_markup=premium_target_keyboard()
    )
    await state.set_state(BuyPremiumStates.choosing_target)

@router.callback_query(lambda c: c.data == "prem_self")
async def prem_self(callback: CallbackQuery, state: FSMContext):
    await state.update_data(target=callback.from_user.username)
    await callback.message.edit_text("📅 Выберите срок:", reply_markup=premium_duration_keyboard())
    await state.set_state(BuyPremiumStates.choosing_duration)

@router.callback_query(lambda c: c.data == "prem_other")
async def prem_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👤 Введите юзернейм друга:", reply_markup=back_button("buy_premium"))
    await state.set_state(BuyPremiumStates.entering_username)

@router.message(BuyPremiumStates.entering_username)
async def process_prem_username(message: types.Message, state: FSMContext):
    username = message.text.replace("@", "").strip()
    await state.update_data(target=username)
    await message.answer("📅 Выберите срок:", reply_markup=premium_duration_keyboard())
    await state.set_state(BuyPremiumStates.choosing_duration)

@router.callback_query(lambda c: c.data.startswith("prem_"), BuyPremiumStates.choosing_duration)
async def process_premium_duration(callback: CallbackQuery, state: FSMContext):
    months = int(callback.data.split("_")[1])
    price_map = {3: 1165, 6: 1555, 12: 2819}
    price_rub = price_map.get(months)
    data = await state.get_data()
    target = data.get("target")
    user = get_user(callback.from_user.id)
    if user.balance < price_rub:
        await callback.answer(f"❌ Недостаточно средств. Нужно: {price_rub} ₽", show_alert=True)
        return
    await callback.message.edit_text("⏳ Покупка Premium через Fragment API...")
    try:
        result = await fragment.purchase_premium(f"@{target}", months)
        if result.get("success"):
            update_balance(callback.from_user.id, -price_rub)
            add_transaction(callback.from_user.id, "premium", price_rub, target_username=target)
            logger.info(f"Пользователь {callback.from_user.id} купил Premium на {months} мес. для @{target}")
            await callback.message.edit_text(
                f"✅ **Premium приобретён!**\n\n👤 @{target}\n📅 {months} мес.\n💰 {price_rub} ₽",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
                ])
            )
        else:
            await callback.message.edit_text(f"❌ Ошибка: {result.get('error')}", reply_markup=error_keyboard("buy_premium"))
        await state.clear()
    except Exception as e:
        logger.exception(f"Ошибка покупки Premium: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=error_keyboard("buy_premium"))