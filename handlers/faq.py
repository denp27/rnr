from aiogram import Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from keyboards.all_keyboards import faq_keyboard, faq_answer_keyboard, back_button

router = Router()

FAQ = {
    "buy_stars": "⭐ **Как купить звёзды:**\n1. Нажмите «Купить звёзды»\n2. Выберите кому\n3. Выберите количество\n4. Подтвердите",
    "buy_premium": "💎 **Как купить Premium:**\n1. Нажмите «Купить Premium»\n2. Выберите кому\n3. Выберите срок\n4. Подтвердите",
    "send_gift": "🎁 **Как подарить подарок:**\n1. Нажмите «Купить подарок»\n2. Выберите получателя\n3. Выберите подарок\n4. Добавьте комментарий\n5. Отправьте",
    "topup": "💰 **Как пополнить баланс:**\n1. Профиль → Пополнить баланс\n2. Введите сумму\n3. Выберите способ оплаты\n4. Оплатите",
    "referral": "👥 **Реферальная программа:**\nПриглашайте друзей по ссылке и получайте 10% от их покупок.",
    "support": "🆘 **Поддержка:** @MstiStarsSupport"
}

@router.callback_query(lambda c: c.data == "faq_menu")
async def faq_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❓ **FAQ**", reply_markup=faq_keyboard())

@router.callback_query(lambda c: c.data.startswith("faq_"))
async def faq_answer(callback: CallbackQuery, state: FSMContext):
    key = callback.data.split("_")[1]
    if key == "back":
        await faq_menu(callback, state)
    elif key == "support_contact":
        await callback.message.edit_text("🆘 Напишите @MstiStarsSupport", reply_markup=back_button("faq_menu"))
    else:
        text = FAQ.get(key, "Информация не найдена")
        await callback.message.edit_text(text, reply_markup=faq_answer_keyboard())
