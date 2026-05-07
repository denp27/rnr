import logging
from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import Config
from database import get_user, update_balance, add_transaction
from services.fragment_client import FragmentClient
from keyboards.all_keyboards import gift_target_keyboard, gift_comment_final_keyboard, gift_comment_with_text_keyboard, back_button, error_keyboard

router = Router()
fragment = FragmentClient()
logger = logging.getLogger(__name__)

class BuyGiftStates(StatesGroup):
    choosing_recipient = State()
    entering_username = State()
    choosing_gift = State()
    adding_comment = State()
    editing_comment = State()

@router.callback_query(lambda c: c.data == "buy_gift")
async def buy_gift(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Пользователь {callback.from_user.id} начал покупку подарка")
    await callback.message.edit_text("🎁 **Покупка подарка**\n\nКому?", reply_markup=gift_target_keyboard())
    await state.set_state(BuyGiftStates.choosing_recipient)

@router.callback_query(lambda c: c.data == "gift_self")
async def gift_self(callback: CallbackQuery, state: FSMContext):
    await state.update_data(recipient=callback.from_user.username)
    await show_gift_list(callback, state)

@router.callback_query(lambda c: c.data == "gift_other")
async def gift_other(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("👤 Введите юзернейм друга:", reply_markup=back_button("buy_gift"))
    await state.set_state(BuyGiftStates.entering_username)

@router.message(BuyGiftStates.entering_username)
async def process_gift_username(message: types.Message, state: FSMContext):
    username = message.text.replace("@", "").strip()
    await state.update_data(recipient=username)
    await show_gift_list(message, state)

async def show_gift_list(event, state: FSMContext):
    gifts = await fragment.get_available_gifts()
    buttons = []
    for gift in gifts[:10]:
        buttons.append([InlineKeyboardButton(text=f"{gift['name']} — {gift['price']} ⭐", callback_data=f"gift_select_{gift['id']}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="buy_gift")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    text = "🎁 Выберите подарок:"
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)
    await state.set_state(BuyGiftStates.choosing_gift)

@router.callback_query(lambda c: c.data.startswith("gift_select_"), BuyGiftStates.choosing_gift)
async def process_gift_selection(callback: CallbackQuery, state: FSMContext):
    gift_id = int(callback.data.split("_")[2])
    gifts = await fragment.get_available_gifts()
    gift = next((g for g in gifts if g["id"] == gift_id), {"name": "Подарок", "price": 50})
    await state.update_data(gift_id=gift_id, gift_name=gift["name"], gift_price=gift["price"])
    await callback.message.edit_text(
        f"💬 **Добавьте комментарий**\n\n🎁 {gift['name']}\n💰 {gift['price']} ⭐\n\nКомментарий до 255 символов.",
        reply_markup=gift_comment_final_keyboard()
    )
    await state.set_state(BuyGiftStates.adding_comment)

@router.callback_query(lambda c: c.data == "add_comment_text", BuyGiftStates.adding_comment)
async def add_comment_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✏️ Введите комментарий:", reply_markup=back_button("buy_gift"))
    await state.set_state(BuyGiftStates.editing_comment)

@router.message(BuyGiftStates.editing_comment)
async def process_comment(message: types.Message, state: FSMContext):
    comment = message.text.strip()
    if len(comment) > 255:
        await message.answer(f"❌ Слишком длинный ({len(comment)}/255)")
        return
    await state.update_data(comment=comment)
    await message.answer(f"📝 Комментарий:\n«{comment}»\n\nВсё верно?", reply_markup=gift_comment_with_text_keyboard(comment))
    await state.set_state(BuyGiftStates.adding_comment)

@router.callback_query(lambda c: c.data == "send_with_comment")
async def send_with_comment(callback: CallbackQuery, state: FSMContext):
    await finalize_gift(callback, state, with_comment=True)

@router.callback_query(lambda c: c.data == "send_without_comment")
async def send_without_comment(callback: CallbackQuery, state: FSMContext):
    await finalize_gift(callback, state, with_comment=False)

async def finalize_gift(callback: CallbackQuery, state: FSMContext, with_comment: bool):
    data = await state.get_data()
    recipient = data.get("recipient")
    gift_price = data.get("gift_price", 50)
    price_rub = gift_price * Config.RUB_PER_STAR
    user = get_user(callback.from_user.id)
    if user.balance < price_rub:
        await callback.answer("❌ Недостаточно средств", show_alert=True)
        return
    update_balance(callback.from_user.id, -price_rub)
    add_transaction(callback.from_user.id, "gift", price_rub, stars_amount=gift_price, target_username=recipient, gift_name=data.get("gift_name"), comment=data.get("comment") if with_comment else None)
    logger.info(f"Пользователь {callback.from_user.id} подарил {data.get('gift_name')} @{recipient} за {price_rub} руб")
    await callback.message.edit_text(f"✅ Подарок отправлен @{recipient}\n💰 {price_rub:.2f} ₽", reply_markup=back_button("main_menu"))
    await state.clear()
