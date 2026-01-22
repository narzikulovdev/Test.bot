import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from bot import dp
from data import db
from bot.states import UserRegistration
from bot.keyboards.inlineKeyboards import get_main_menu_keyboard, get_registration_skip_keyboard

logger = logging.getLogger(__name__)

# Команда /start
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message, state: FSMContext, is_new_user: bool = False):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name

    # Проверяем, есть ли полная информация о пользователе
    user_info = db.Users.getUserFullInfo(user_id)

    if not user_info or not user_info.get('firstName') or not user_info.get('phone'):
        # Пользователь не зарегистрирован полностью
        text = f"👋 Привет, {user_name}!\n\n" \
               "Для полноценного использования бота нужно пройти регистрацию.\n\n" \
               "📝 Введите ваше имя:"

        await UserRegistration.waiting_for_first_name.set()
        await message.reply(text, reply_markup=get_registration_skip_keyboard())
    else:
        # Пользователь зарегистрирован, показываем главное меню
        text = f"👋 С возвращением, {user_info['firstName']}!\n\n" \
               "Выберите действие:"

        await message.reply(text, reply_markup=get_main_menu_keyboard())
        await state.finish()


# Обработчик пропуска регистрации
@dp.callback_query_handler(lambda c: c.data == 'skip_registration', state='*')
async def skip_registration(callback_query: types.CallbackQuery, state: FSMContext):
    """Пропуск регистрации"""
    await callback_query.answer()

    text = "Вы можете пройти регистрацию позже в любое время.\n\n" \
           "Выберите действие:"

    await callback_query.message.edit_text(text, reply_markup=get_main_menu_keyboard())
    await state.finish()


# Регистрация - имя
@dp.message_handler(state=UserRegistration.waiting_for_first_name)
async def process_first_name(message: types.Message, state: FSMContext):
    """Обработка ввода имени"""
    first_name = message.text.strip()

    if len(first_name) < 2:
        await message.reply("❌ Имя должно содержать минимум 2 символа. Попробуйте еще раз:")
        return

    await state.update_data(first_name=first_name)

    text = "✅ Имя сохранено!\n\n" \
           "📝 Теперь введите вашу фамилию:"

    await UserRegistration.waiting_for_last_name.set()
    await message.reply(text, reply_markup=get_registration_skip_keyboard())


# Регистрация - фамилия
@dp.message_handler(state=UserRegistration.waiting_for_last_name)
async def process_last_name(message: types.Message, state: FSMContext):
    """Обработка ввода фамилии"""
    last_name = message.text.strip()

    if len(last_name) < 2:
        await message.reply("❌ Фамилия должна содержать минимум 2 символа. Попробуйте еще раз:")
        return

    await state.update_data(last_name=last_name)

    text = "✅ Фамилия сохранена!\n\n" \
           "📝 Теперь введите ваше отчество (или нажмите 'Пропустить'):"

    await UserRegistration.waiting_for_middle_name.set()
    await message.reply(text, reply_markup=get_registration_skip_keyboard())


# Регистрация - отчество
@dp.message_handler(state=UserRegistration.waiting_for_middle_name)
async def process_middle_name(message: types.Message, state: FSMContext):
    """Обработка ввода отчества"""
    middle_name = message.text.strip()

    if len(middle_name) < 2:
        await message.reply("❌ Отчество должно содержать минимум 2 символа. Попробуйте еще раз:")
        return

    await state.update_data(middle_name=middle_name)

    text = "✅ Отчество сохранено!\n\n" \
           "📱 Теперь введите ваш номер телефона в формате +7XXXXXXXXXX:"

    await UserRegistration.waiting_for_phone.set()
    await message.reply(text, reply_markup=get_registration_skip_keyboard())


# Регистрация - телефон
@dp.message_handler(state=UserRegistration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка ввода телефона"""
    phone = message.text.strip()

    # Простая валидация телефона
    if not phone.startswith('+') or len(phone) < 11:
        await message.reply("❌ Номер телефона должен быть в формате +7XXXXXXXXXX. Попробуйте еще раз:")
        return

    # Сохраняем все данные
    user_data = await state.get_data()
    user_data['phone'] = phone

    # Обновляем информацию пользователя в БД
    db.Users.updateUserInfo(
        message.from_user.id,
        firstName=user_data.get('first_name'),
        lastName=user_data.get('last_name'),
        middleName=user_data.get('middle_name'),
        phone=phone
    )

    text = "✅ Регистрация завершена!\n\n" \
           "Теперь вы можете пользоваться всеми функциями бота.\n\n" \
           "Выберите действие:"

    await message.reply(text, reply_markup=get_main_menu_keyboard())
    await state.finish()


# Команда /menu для возврата в главное меню
@dp.message_handler(commands=['menu'])
async def menu_command(message: types.Message, state: FSMContext):
    """Команда для возврата в главное меню"""
    user_info = db.Users.getUserFullInfo(message.from_user.id)

    if user_info and user_info.get('firstName'):
        name = user_info['firstName']
    else:
        name = message.from_user.first_name

    text = f"👋 {name}!\n\n" \
           "Выберите действие:"

    await message.reply(text, reply_markup=get_main_menu_keyboard())
    await state.finish()
