import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import get_user, update_balance, add_transaction, Session, ChannelWithdrawal
from services.fragment_client import FragmentClient
from keyboards.all_keyboards import channel_stars_keyboard, channel_balance_actions_keyboard, back_button, withdrawal_success_keyboard, error_keyboard

router = Router()
fragment = FragmentClient()
logger = logging.getLogger(__name__)

class ChannelStarsStates(StatesGroup):
    choosing_channel = State()
    entering_amount = State()
    confirming = State()

@router.callback_query(lambda c: c.data == "channel_stars")
async def channel_stars_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📡 Управление звёздами канала", reply_markup=channel_stars_keyboard())

@router.callback_query(lambda c: c.data == "channel_balance")
async def channel_balance(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("📡 Введите username канала:", reply_markup=back_button("channel_stars"))
    await state.set_state(ChannelStarsStates.choosing_channel)

@router.message(ChannelStarsStates.choosing_channel)
async def process_channel_username(message: types.Message, state: FSMContext):
    channel = message.text.replace("@", "").strip()
    loading = await message.answer("⏳ Получение баланса...")
    try:
        balance_data = await fragment.get_channel_stars_balance(channel)
        if not balance_data.get("success"):
            await loading.edit_text(f"❌ Ошибка: {balance_data.get('error')}", reply_markup=error_keyboard("channel_balance"))
            return
        await state.update_data(current_channel=channel, balance=balance_data.get("balance", 0))
        rub = balance_data.get("balance", 0) * Config.RUB_PER_STAR
        await loading.edit_text(
            f"📊 Баланс @{channel}\n⭐ {balance_data.get('balance', 0)}\n💰 {rub:.2f} ₽",
            reply_markup=channel_balance_actions_keyboard()
        )
    except Exception as e:
        logger.exception(f"Ошибка получения баланса канала: {e}")
        await loading.edit_text(f"❌ Ошибка: {e}", reply_markup=error_keyboard("channel_balance"))

@router.callback_query(lambda c: c.data == "channel_withdraw")
async def start_withdraw(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    channel = data.get("current_channel")
    if not channel:
        await callback.message.edit_text("❌ Сначала выберите канал", reply_markup=back_button("channel_stars"))
        return
    balance = data.get("balance", 0)
    await callback.message.edit_text(
        f"💸 Вывод @{channel}\n⭐ Доступно: {balance}\n💰 Курс 1⭐={Config.RUB_PER_STAR}₽\n\nВведите кол-во (мин {Config.MIN_WITHDRAW_STARS}):",
        reply_markup=back_button("channel_stars")
    )
    await state.set_state(ChannelStarsStates.entering_amount)

@router.message(ChannelStarsStates.entering_amount)
async def process_withdraw_amount(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        data = await state.get_data()
        balance = data.get("balance", 0)
        if amount < Config.MIN_WITHDRAW_STARS or amount > balance:
            await message.answer(f"❌ Некорректная сумма. Доступно {balance} ⭐")
            return
        rub = amount * Config.RUB_PER_STAR
        await state.update_data(withdraw_amount=amount, withdraw_rub=rub)
        await message.answer(
            f"📝 Подтверждение\n📡 @{data['current_channel']}\n⭐ {amount}\n💰 {rub:.2f} ₽\n\nПодтверждаете?",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_withdraw")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="channel_stars")]
            ])
        )
        await state.set_state(ChannelStarsStates.confirming)
    except ValueError:
        await message.answer("❌ Введите целое число")

@router.callback_query(lambda c: c.data == "confirm_withdraw")
async def confirm_withdraw(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    channel = data.get("current_channel")
    amount = data.get("withdraw_amount")
    rub = data.get("withdraw_rub")
    if not channel or not amount:
        await callback.message.edit_text("❌ Ошибка", reply_markup=back_button("channel_stars"))
        return
    await callback.message.edit_text("⏳ Вывод через Fragment...")
    try:
        result = await fragment.withdraw_channel_stars(channel, amount, destination="balance")
        if result.get("success"):
            update_balance(callback.from_user.id, rub)
            add_transaction(callback.from_user.id, "channel_withdraw", rub, stars_amount=amount, target_username=channel)
            session = Session()
            wd = ChannelWithdrawal(user_id=callback.from_user.id, channel_username=channel, stars_amount=amount, rub_amount=rub, status="completed")
            session.add(wd)
            session.commit()
            session.close()
            logger.info(f"Пользователь {callback.from_user.id} вывел {amount} звёзд с канала {channel}")
            await callback.message.edit_text(f"✅ Выведено {amount} ⭐\n💰 {rub:.2f} ₽ зачислено", reply_markup=withdrawal_success_keyboard())
        else:
            await callback.message.edit_text(f"❌ Ошибка: {result.get('error')}", reply_markup=error_keyboard("channel_withdraw"))
    except Exception as e:
        logger.exception(f"Ошибка вывода звёзд: {e}")
        await callback.message.edit_text(f"❌ Ошибка: {e}", reply_markup=error_keyboard("channel_withdraw"))
    await state.clear()