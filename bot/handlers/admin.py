import logging
from aiogram import types
from aiogram.dispatcher import FSMContext
from bot import dp
from data import db
from bot.states import AdminPanel
from bot.keyboards.inlineKeyboards import (
    get_admin_main_keyboard, get_admin_categories_keyboard,
    get_admin_tests_keyboard, get_admin_category_selection_keyboard,
    get_admin_questions_keyboard, get_admin_answers_keyboard,
    get_admin_stats_keyboard, get_admin_user_actions_keyboard,
    get_confirmation_keyboard, get_main_menu_keyboard
)

logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь админом"""
    user = db.Users.getUserById(user_id)
    return user and user.get('role') == 'admin'


# Команда /admin для входа в админ-панель
@dp.message_handler(commands=['admin'])
async def admin_command(message: types.Message, state: FSMContext):
    """Вход в админ-панель"""
    if not is_admin(message.from_user.id):
        await message.reply("❌ У вас нет прав доступа к админ-панели.")
        return

    text = "👑 Админ-панель\n\n" \
           "Выберите действие:"

    await message.reply(text, reply_markup=get_admin_main_keyboard())
    await AdminPanel.main_menu.set()


# Вход в админ-панель через callback
@dp.callback_query_handler(lambda c: c.data.startswith('admin_'), state='*')
async def admin_panel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик админ-панели"""
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("❌ Нет доступа")
        return

    await callback_query.answer()
    action = callback_query.data

    if action == 'admin_back_to_main':
        # Возврат в главное меню админа
        text = "👑 Админ-панель\n\n" \
               "Выберите действие:"
        await callback_query.message.edit_text(text, reply_markup=get_admin_main_keyboard())
        await AdminPanel.main_menu.set()

    elif action == 'admin_categories':
        # Управление категориями
        await show_admin_categories(callback_query)

    elif action == 'admin_tests':
        # Управление тестами
        await show_admin_tests(callback_query)

    elif action == 'admin_stats':
        # Статистика
        await show_admin_stats(callback_query)

    elif action == 'admin_broadcast':
        # Рассылка
        await start_broadcast(callback_query, state)

    elif action == 'admin_block_users':
        # Блокировка пользователей
        await show_user_blocking_menu(callback_query, state)

    elif action == 'exit_admin':
        # Выход из админки
        text = "👋 Выход из админ-панели.\n\n" \
               "Выберите действие:"
        await callback_query.message.edit_text(text, reply_markup=get_main_menu_keyboard())
        await state.finish()


# ==================== УПРАВЛЕНИЕ КАТЕГОРИЯМИ ====================

async def show_admin_categories(callback_query: types.CallbackQuery):
    """Показать управление категориями"""
    categories = db.Categories.getAllCategories(active_only=False)

    text = "📂 Управление категориями\n\n"

    if not categories:
        text += "Категорий пока нет."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_categories_keyboard(categories)
    )


@dp.callback_query_handler(lambda c: c.data == 'admin_add_category', state='*')
async def add_category(callback_query: types.CallbackQuery, state: FSMContext):
    """Добавление новой категории"""
    await callback_query.answer()

    text = "📝 Введите название новой категории:"
    await callback_query.message.edit_text(text)

    await AdminPanel.adding_category_name.set()


@dp.message_handler(state=AdminPanel.adding_category_name)
async def process_category_name(message: types.Message, state: FSMContext):
    """Обработка названия категории"""
    category_name = message.text.strip()

    if len(category_name) < 2:
        await message.reply("❌ Название категории должно содержать минимум 2 символа.")
        return

    # Сохраняем название и спрашиваем описание
    await state.update_data(category_name=category_name)

    text = "📝 Теперь введите описание категории (или '-' для пропуска):"
    await AdminPanel.adding_category_description.set()
    await message.reply(text)


@dp.message_handler(state=AdminPanel.adding_category_description)
async def process_category_description(message: types.Message, state: FSMContext):
    """Обработка описания категории"""
    description = message.text.strip()
    if description == '-':
        description = None

    state_data = await state.get_data()
    category_name = state_data['category_name']

    # Добавляем категорию
    category_id = db.Categories.addCategory(category_name, description)

    if category_id:
        text = f"✅ Категория '{category_name}' успешно добавлена!"
    else:
        text = "❌ Ошибка при добавлении категории."

    await message.reply(text, reply_markup=get_admin_main_keyboard())
    await AdminPanel.main_menu.set()


@dp.callback_query_handler(lambda c: c.data.startswith('admin_delete_category_'), state='*')
async def delete_category(callback_query: types.CallbackQuery, state: FSMContext):
    """Удаление категории"""
    await callback_query.answer()

    category_id = int(callback_query.data.split('_')[-1])
    category = db.Categories.getCategoryById(category_id)

    if not category:
        await callback_query.message.edit_text("❌ Категория не найдена.")
        return

    text = f"🗑️ Вы уверены, что хотите удалить категорию '{category['name']}'?\n\n" \
           "Все тесты в этой категории также будут скрыты."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_confirmation_keyboard('delete_category', category_id)
    )


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_delete_category_'), state='*')
async def confirm_delete_category(callback_query: types.CallbackQuery, state: FSMContext):
    """Подтверждение удаления категории"""
    await callback_query.answer()

    category_id = int(callback_query.data.split('_')[-1])

    if db.Categories.deleteCategory(category_id):
        text = "✅ Категория успешно удалена."
    else:
        text = "❌ Ошибка при удалении категории."

    categories = db.Categories.getAllCategories(active_only=False)
    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_categories_keyboard(categories)
    )


# ==================== УПРАВЛЕНИЕ ТЕСТАМИ ====================

async def show_admin_tests(callback_query: types.CallbackQuery):
    """Показать управление тестами"""
    tests = db.Tests.getAllTests(active_only=False)

    text = "📝 Управление тестами\n\n"

    if not tests:
        text += "Тестов пока нет."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_tests_keyboard(tests)
    )


@dp.callback_query_handler(lambda c: c.data == 'admin_add_test', state='*')
async def add_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Добавление нового теста"""
    await callback_query.answer()

    categories = db.Categories.getAllCategories()
    if not categories:
        await callback_query.message.edit_text(
            "❌ Сначала нужно создать хотя бы одну категорию.",
            reply_markup=get_admin_main_keyboard()
        )
        return

    text = "📂 Выберите категорию для нового теста:"
    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_category_selection_keyboard(categories)
    )

    await AdminPanel.choosing_category_for_test.set()


@dp.callback_query_handler(lambda c: c.data.startswith('admin_select_category_'), state=AdminPanel.choosing_category_for_test)
async def select_category_for_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Выбор категории для теста"""
    await callback_query.answer()

    category_id = int(callback_query.data.split('_')[-1])
    await state.update_data(selected_category_id=category_id)

    text = "📝 Введите название нового теста:"
    await callback_query.message.edit_text(text)

    await AdminPanel.adding_test_title.set()


@dp.message_handler(state=AdminPanel.adding_test_title)
async def process_test_title(message: types.Message, state: FSMContext):
    """Обработка названия теста"""
    test_title = message.text.strip()

    if len(test_title) < 2:
        await message.reply("❌ Название теста должно содержать минимум 2 символа.")
        return

    await state.update_data(test_title=test_title)

    text = "📝 Введите описание теста (или '-' для пропуска):"
    await AdminPanel.adding_test_description.set()
    await message.reply(text)


@dp.message_handler(state=AdminPanel.adding_test_description)
async def process_test_description(message: types.Message, state: FSMContext):
    """Обработка описания теста"""
    description = message.text.strip()
    if description == '-':
        description = None

    state_data = await state.get_data()
    category_id = state_data['selected_category_id']
    test_title = state_data['test_title']

    # Добавляем тест
    test_id = db.Tests.addTest(category_id, test_title, description)

    if test_id:
        text = f"✅ Тест '{test_title}' успешно добавлен!"
    else:
        text = "❌ Ошибка при добавлении теста."

    await message.reply(text, reply_markup=get_admin_main_keyboard())
    await AdminPanel.main_menu.set()


@dp.callback_query_handler(lambda c: c.data.startswith('admin_edit_test_'), state='*')
async def edit_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Редактирование теста - показ вопросов"""
    await callback_query.answer()

    test_id = int(callback_query.data.split('_')[-1])
    test = db.Tests.getTestById(test_id)

    if not test:
        await callback_query.message.edit_text("❌ Тест не найден.")
        return

    questions = db.Questions.getQuestionsByTest(test_id)

    text = f"📝 Управление вопросами теста '{test['title']}'\n\n"

    if not questions:
        text += "Вопросов пока нет."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_questions_keyboard(questions, test_id)
    )


@dp.callback_query_handler(lambda c: c.data.startswith('admin_delete_test_'), state='*')
async def delete_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Удаление теста"""
    await callback_query.answer()

    test_id = int(callback_query.data.split('_')[-1])
    test = db.Tests.getTestById(test_id)

    if not test:
        await callback_query.message.edit_text("❌ Тест не найден.")
        return

    text = f"🗑️ Вы уверены, что хотите удалить тест '{test['title']}'?\n\n" \
           "Все вопросы и результаты будут скрыты."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_confirmation_keyboard('delete_test', test_id)
    )


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_delete_test_'), state='*')
async def confirm_delete_test(callback_query: types.CallbackQuery, state: FSMContext):
    """Подтверждение удаления теста"""
    await callback_query.answer()

    test_id = int(callback_query.data.split('_')[-1])

    if db.Tests.deleteTest(test_id):
        text = "✅ Тест успешно удален."
    else:
        text = "❌ Ошибка при удалении теста."

    tests = db.Tests.getAllTests(active_only=False)
    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_tests_keyboard(tests)
    )


# ==================== УПРАВЛЕНИЕ ВОПРОСАМИ ====================

@dp.callback_query_handler(lambda c: c.data.startswith('admin_add_question_'), state='*')
async def add_question(callback_query: types.CallbackQuery, state: FSMContext):
    """Добавление вопроса"""
    await callback_query.answer()

    test_id = int(callback_query.data.split('_')[-1])
    await state.update_data(current_test_id=test_id)

    text = "❓ Введите текст вопроса:"
    await callback_query.message.edit_text(text)

    await AdminPanel.adding_question_text.set()


@dp.message_handler(state=AdminPanel.adding_question_text)
async def process_question_text(message: types.Message, state: FSMContext):
    """Обработка текста вопроса"""
    question_text = message.text.strip()

    if len(question_text) < 5:
        await message.reply("❌ Текст вопроса должен содержать минимум 5 символов.")
        return

    await state.update_data(question_text=question_text)

    text = "🖼️ Отправьте изображение для вопроса (или введите '-' для пропуска):"
    await AdminPanel.adding_question_image.set()
    await message.reply(text)


@dp.message_handler(content_types=['photo', 'text'], state=AdminPanel.adding_question_image)
async def process_question_image(message: types.Message, state: FSMContext):
    """Обработка изображения вопроса"""
    state_data = await state.get_data()
    question_text = state_data['question_text']
    test_id = state_data['current_test_id']

    image_path = None
    if message.photo:
        # Здесь можно реализовать сохранение изображения
        # image_path = save_image(message.photo[-1])
        pass
    elif message.text and message.text.strip() != '-':
        await message.reply("❌ Отправьте изображение или введите '-' для пропуска.")
        return

    # Добавляем вопрос
    question_id = db.Questions.addQuestion(test_id, question_text, image_path)

    if question_id:
        text = "✅ Вопрос успешно добавлен!\n\n" \
               "Теперь добавьте варианты ответов для этого вопроса."

        # Показываем управление ответами
        answers = db.Answers.getAnswersByQuestion(question_id)
        await message.reply(
            text,
            reply_markup=get_admin_answers_keyboard(answers, question_id)
        )
        await AdminPanel.main_menu.set()
    else:
        await message.reply("❌ Ошибка при добавлении вопроса.", reply_markup=get_admin_main_keyboard())
        await AdminPanel.main_menu.set()


# ==================== УПРАВЛЕНИЕ ОТВЕТАМИ ====================

@dp.callback_query_handler(lambda c: c.data.startswith('admin_add_answer_'), state='*')
async def add_answer(callback_query: types.CallbackQuery, state: FSMContext):
    """Добавление ответа"""
    await callback_query.answer()

    question_id = int(callback_query.data.split('_')[-1])
    await state.update_data(current_question_id=question_id)

    text = "📝 Введите текст ответа:"
    await callback_query.message.edit_text(text)

    await AdminPanel.adding_answer_text.set()


@dp.message_handler(state=AdminPanel.adding_answer_text)
async def process_answer_text(message: types.Message, state: FSMContext):
    """Обработка текста ответа"""
    answer_text = message.text.strip()

    if len(answer_text) < 1:
        await message.reply("❌ Текст ответа не может быть пустым.")
        return

    state_data = await state.get_data()
    question_id = state_data['current_question_id']

    # Проверяем, есть ли уже правильный ответ
    existing_answers = db.Answers.getAnswersByQuestion(question_id)
    has_correct = any(answer['is_correct'] for answer in existing_answers)

    if not has_correct:
        # Если правильного ответа нет, предлагаем сделать этот правильным
        text = f"✅ Сделать этот ответ правильным?\n\n" \
               f"Ответ: {answer_text}"

        await state.update_data(answer_text=answer_text)
        await message.reply(text, reply_markup=get_confirmation_keyboard('set_correct_answer', 'yes'))
        await AdminPanel.marking_correct_answer.set()
    else:
        # Добавляем неправильный ответ
        answer_id = db.Answers.addAnswer(question_id, answer_text, False)
        if answer_id:
            text = "✅ Неправильный ответ добавлен!"
        else:
            text = "❌ Ошибка при добавлении ответа."

        answers = db.Answers.getAnswersByQuestion(question_id)
        await message.reply(text, reply_markup=get_admin_answers_keyboard(answers, question_id))
        await AdminPanel.main_menu.set()


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_set_correct_answer_'), state=AdminPanel.marking_correct_answer)
async def set_correct_answer(callback_query: types.CallbackQuery, state: FSMContext):
    """Установка правильного ответа"""
    await callback_query.answer()

    state_data = await state.get_data()
    question_id = state_data['current_question_id']
    answer_text = state_data['answer_text']

    is_correct = callback_query.data.endswith('yes')

    answer_id = db.Answers.addAnswer(question_id, answer_text, is_correct)

    if answer_id:
        status = "правильным" if is_correct else "неправильным"
        text = f"✅ {status.capitalize()} ответ добавлен!"
    else:
        text = "❌ Ошибка при добавлении ответа."

    answers = db.Answers.getAnswersByQuestion(question_id)
    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_answers_keyboard(answers, question_id)
    )

    await AdminPanel.main_menu.set()


# ==================== СТАТИСТИКА ====================

async def show_admin_stats(callback_query: types.CallbackQuery):
    """Показать статистику"""
    text = "📊 Выберите период для просмотра статистики:"
    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_stats_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data.startswith('stats_'), state='*')
async def show_stats_period(callback_query: types.CallbackQuery, state: FSMContext):
    """Показать статистику за период"""
    await callback_query.answer()

    period = callback_query.data.split('_')[1]

    period_map = {
        'week': (7, 'неделю'),
        'month': (30, 'месяц'),
        'year': (365, 'год'),
        'all': (None, 'весь период')
    }

    days, period_name = period_map.get(period, (None, 'весь период'))

    # Получаем статистику
    test_stats = db.TestResults.getTestStats(period_days=days)
    user_stats = db.Users.getStats()

    text = f"📊 Статистика за {period_name}:\n\n" \
           "👥 Пользователи:\n" \
           f"• Всего: {user_stats['total_users']}\n" \
           f"• Новых за неделю: {user_stats['new_users_week']}\n" \
           f"• Заблокированных: {user_stats['blocked_users']}\n" \
           f"• Администраторов: {user_stats['admins_count']}\n\n" \
           "📝 Тесты:\n" \
           f"• Пройдено тестов: {test_stats['total_passed']}\n" \
           f"• Уникальных пользователей: {test_stats['unique_users']}\n" \
           f"• Средний балл: {test_stats['avg_score']}%\n"

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_stats_keyboard()
    )


# ==================== РАССЫЛКА ====================

async def start_broadcast(callback_query: types.CallbackQuery, state: FSMContext):
    """Начало рассылки"""
    text = "📢 Введите сообщение для рассылки всем пользователям:"
    await callback_query.message.edit_text(text)

    await AdminPanel.writing_broadcast_message.set()


@dp.message_handler(state=AdminPanel.writing_broadcast_message)
async def process_broadcast_message(message: types.Message, state: FSMContext):
    """Обработка сообщения для рассылки"""
    broadcast_text = message.text

    text = f"📢 Подтвердите рассылку сообщения:\n\n" \
           f"\"{broadcast_text}\"\n\n" \
           "Сообщение будет отправлено всем пользователям бота."

    await message.reply(
        text,
        reply_markup=get_confirmation_keyboard('broadcast', 'send')
    )


@dp.callback_query_handler(lambda c: c.data.startswith('confirm_broadcast_'), state='*')
async def confirm_broadcast(callback_query: types.CallbackQuery, state: FSMContext):
    """Подтверждение рассылки"""
    await callback_query.answer()

    if not callback_query.data.endswith('send'):
        await callback_query.message.edit_text(
            "❌ Рассылка отменена.",
            reply_markup=get_admin_main_keyboard()
        )
        await AdminPanel.main_menu.set()
        return

    # Получаем сообщение из состояния (нужно сохранить его)
    # Здесь нужно реализовать логику сохранения сообщения для рассылки
    # Для простоты отправим тестовое сообщение
    from bot import bot

    users = db.Users.getAllUsers()
    sent_count = 0
    failed_count = 0

    broadcast_message = "📢 Администратор разослал сообщение:\n\nТестовое сообщение для всех пользователей!"

    for user in users:
        if not user['isBlocked']:  # Не отправляем заблокированным
            try:
                await bot.send_message(user['userId'], broadcast_message)
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send broadcast to {user['userId']}: {e}")
                failed_count += 1

    text = f"✅ Рассылка завершена!\n\n" \
           f"📤 Отправлено: {sent_count}\n" \
           f"❌ Ошибок: {failed_count}"

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard()
    )

    await AdminPanel.main_menu.set()


# ==================== БЛОКИРОВКА ПОЛЬЗОВАТЕЛЕЙ ====================

async def show_user_blocking_menu(callback_query: types.CallbackQuery, state: FSMContext):
    """Показать меню блокировки пользователей"""
    text = "🚫 Управление пользователями\n\n" \
           "Введите номер телефона пользователя в формате +7XXXXXXXXXX:"
    await callback_query.message.edit_text(text)

    await AdminPanel.entering_user_phone_for_block.set()


@dp.message_handler(state=AdminPanel.entering_user_phone_for_block)
async def process_user_phone_for_block(message: types.Message, state: FSMContext):
    """Обработка телефона пользователя для блокировки"""
    phone = message.text.strip()

    # Ищем пользователя по телефону
    # Предполагаем, что у нас есть индекс или поиск по телефону
    # Для простоты ищем в таблице пользователей
    connect = db.getConnection()
    if connect:
        try:
            cursor = connect.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
            user = cursor.fetchone()

            if not user:
                await message.reply(
                    "❌ Пользователь с таким номером телефона не найден.",
                    reply_markup=get_admin_main_keyboard()
                )
                await AdminPanel.main_menu.set()
                return

            # Показываем информацию о пользователе и действия
            user_info = user
            status = "🚫 Заблокирован" if user['isBlocked'] else "✅ Активен"
            admin_status = "👑 Админ" if user['role'] == 'admin' else "👤 Пользователь"

            text = f"👤 Информация о пользователе:\n\n" \
                   f"📱 Телефон: {user['phone']}\n" \
                   f"👤 Имя: {user['firstName'] or 'Не указано'} {user['lastName'] or ''}\n" \
                   f"🔹 Статус: {status}\n" \
                   f"🔹 Роль: {admin_status}\n" \
                   f"📅 Регистрация: {user['joinDate']}\n\n" \
                   "Выберите действие:"

            await message.reply(
                text,
                reply_markup=get_admin_user_actions_keyboard(user_info)
            )

        finally:
            connect.close()

    await AdminPanel.main_menu.set()


@dp.callback_query_handler(lambda c: c.data.startswith('admin_block_user_'), state='*')
async def block_user(callback_query: types.CallbackQuery, state: FSMContext):
    """Блокировка пользователя"""
    await callback_query.answer()

    user_id = int(callback_query.data.split('_')[-1])

    if db.Users.blockUser(user_id):
        text = "✅ Пользователь заблокирован."
    else:
        text = "❌ Ошибка при блокировке пользователя."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data.startswith('admin_unblock_user_'), state='*')
async def unblock_user(callback_query: types.CallbackQuery, state: FSMContext):
    """Разблокировка пользователя"""
    await callback_query.answer()

    user_id = int(callback_query.data.split('_')[-1])

    if db.Users.unblockUser(user_id):
        text = "✅ Пользователь разблокирован."
    else:
        text = "❌ Ошибка при разблокировке пользователя."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data.startswith('admin_make_admin_'), state='*')
async def make_admin(callback_query: types.CallbackQuery, state: FSMContext):
    """Назначение администратора"""
    await callback_query.answer()

    user_id = int(callback_query.data.split('_')[-1])

    if db.Users.setAdmin(user_id):
        text = "✅ Пользователь назначен администратором."
    else:
        text = "❌ Ошибка при назначении администратора."

    await callback_query.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard()
    )


@dp.callback_query_handler(lambda c: c.data == 'admin_back_to_block_users', state='*')
async def back_to_block_users(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к меню блокировки"""
    await callback_query.answer()

    text = "🚫 Управление пользователями\n\n" \
           "Введите номер телефона пользователя в формате +7XXXXXXXXXX:"
    await callback_query.message.edit_text(text)

    await AdminPanel.entering_user_phone_for_block.set()


# ==================== ОБЩИЕ ОБРАБОТЧИКИ ====================

@dp.callback_query_handler(lambda c: c.data == 'cancel_', state='*')
async def cancel_action(callback_query: types.CallbackQuery, state: FSMContext):
    """Отмена действия"""
    await callback_query.answer("❌ Действие отменено")

    # Возврат в админ-панель
    text = "👑 Админ-панель\n\n" \
           "Выберите действие:"
    await callback_query.message.edit_text(text, reply_markup=get_admin_main_keyboard())
    await AdminPanel.main_menu.set()


@dp.callback_query_handler(lambda c: c.data.startswith('admin_back_to_questions_'), state='*')
async def back_to_questions(callback_query: types.CallbackQuery, state: FSMContext):
    """Возврат к вопросам"""
    await callback_query.answer()

    question_id = int(callback_query.data.split('_')[-1])

    # Получаем test_id из вопроса
    question = db.Questions.getQuestionById(question_id)
    if question:
        questions = db.Questions.getQuestionsByTest(question['test_id'])
        await callback_query.message.edit_text(
            f"📝 Управление вопросами\n\n",
            reply_markup=get_admin_questions_keyboard(questions, question['test_id'])
        )
