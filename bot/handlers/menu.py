import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from bot import dp
from data import db
from bot.keyboards.inlineKeyboards import get_main_menu_keyboard

logger = logging.getLogger(__name__)


# Обработчик главного меню
@dp.callback_query_handler(lambda c: c.data == 'back_to_menu', state='*')
@dp.callback_query_handler(lambda c: c.data == 'take_test', state='*')
@dp.callback_query_handler(lambda c: c.data == 'support', state='*')
@dp.callback_query_handler(lambda c: c.data == 'about_bot', state='*')
async def main_menu_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик главного меню"""
    await callback_query.answer()
    action = callback_query.data

    user_info = db.Users.getUserFullInfo(callback_query.from_user.id)
    name = user_info['firstName'] if user_info and user_info.get('firstName') else callback_query.from_user.first_name

    if action == 'take_test':
        # Переход к выбору тестов будет реализован в другом handler'е
        await callback_query.message.edit_text(
            "Выберите категорию для прохождения теста:",
            reply_markup=None  # Клавиатура будет добавлена в handler'е тестов
        )
        # Здесь будет логика перехода к тестам

    elif action == 'support':
        text = "📞 Поддержка\n\n" \
               "Если у вас возникли вопросы или проблемы, свяжитесь с администратором:\n\n" \
               "💬 Напишите в поддержку: @support_username\n\n" \
               "Мы постараемся ответить как можно скорее!"

        await callback_query.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )

    elif action == 'about_bot':
        text = "ℹ️ О боте\n\n" \
               "🤖 Этот бот предназначен для прохождения тестов по различным категориям.\n\n" \
               "📚 Функции:\n" \
               "• Прохождение тестов\n" \
               "• Просмотр результатов\n" \
               "• Поддержка различных категорий\n\n" \
               "👨‍💼 Для администраторов доступны:\n" \
               "• Управление тестами и категориями\n" \
               "• Статистика\n" \
               "• Рассылка сообщений\n" \
               "• Блокировка пользователей"

        await callback_query.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )

    elif action == 'back_to_menu':
        text = f"👋 {name}!\n\n" \
               "Выберите действие:"

        await callback_query.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard()
        )

    await state.finish()
