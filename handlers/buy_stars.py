import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery

from config import Config
from database import get_user, update_balance, add_transaction
from services.fragment_client import FragmentClient
from keyboards.all_keyboards import stars_target_keyboard, stars_amount_keyboard, back_button, error_keyboard

router = Router()
fragment = FragmentClient()
logger = logging.getLogger(__name__)

class BuyStarsStates(StatesGroup):
    choosing_target = State()
    entering_username = State()
    choosing_amount = State()

@router.callback_query(lambda c: c.data == "buy_stars")
async def buy_stars(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    logger.info(f"Пользователь {callback.from_user.id} начал покупку звёзд")
    await callback.message.edit_text(
        f"⭐ **Покупка звёзд** ⭐\n\n💰 Баланс: {user.balance:.2f} ₽\n💎 Курс: 1 ⭐ = {Config.RUB_PER_STAR} ₽\n\n👥 Выберите кому:",
        reply_markup=stars_target_keyboard()
    )
    await state.set_state(BuyStarsStates.choosing_target)

@router.callback_query(lambda c: c.data == "stars_self")
async def stars_self(callback: CallbackQuery, state: FSMContext):
    await state.update_data(target=callback.from_user.username)
    await callback.message.edit_text("⭐ Выберите количество звёзд:", reply_markup=stars_amount_keyboard())
    await state.set_state(BuyStarsStates.choosing_amount)

@router.callback_query(lambda c: c.data == "stars_other")
async def stars_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👤 Введите юзернейм друга:", reply_markup=back_button("buy_stars"))
    await state.set_state(BuyStarsStates.entering_username)

@router.message(BuyStarsStates.entering_username)
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.replace("@", "").strip()
    await state.update_data(target=username)
    await message.answer("⭐ Выберите количество звёзд:", reply_markup=stars_amount_keyboard())
    await state.set_state(BuyStarsStates.choosing_amount)

@router.callback_query(lambda c: c.data.startswith("stars_"), BuyStarsStates.choosing_amount)
async def process_stars_amount(callback: CallbackQuery, state: FSMContext):
    stars = int(callback.data.split("_")[1])
    price_rub = stars * Config.RUB_PER_STAR
    data = await state.get_data()
    target = data.get("target")
    user = get_user(callback.from_user.id)
    if user.balance < price_rub:
        await callback.answer(f"❌ Недостаточно средств. Нужно: {price_rub:.2f} ₽", show_alert=True)
        return
    await callback.message.edit_text("⏳ Отправка звёзд через Fragment API...")
    try:
        result = await fragment.purchase_stars(f"@{target}", stars)
        if result.get("success"):
            update_balance(callback.from_user.id, -price_rub)
            add_transaction(callback.from_user.id, "stars", price_rub, stars_amount=stars, target_username=target)
            logger.info(f"Пользователь {callback.from_user.id} купил {stars} звёзд для @{target}")
            await callback.message.edit_text(
                f"✅ **Успешно!**\n\n⭐ {stars} звёзд отправлено @{target}\n💰 {price_rub:.2f} ₽",
                reply_markup=back_button("main_menu")
            )
        else:
            await callback.message.edit_text(f"❌ Ошибка: {result.get('error')}", reply_markup=error_keyboard("buy_stars"))
        await state.clear()
    except Exception as e:
        logger.exception(f"Ошибка покупки звёзд: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {str(e)}", reply_markup=error_keyboard("buy_stars"))
