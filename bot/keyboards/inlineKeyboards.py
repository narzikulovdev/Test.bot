from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Главное меню пользователя
def get_main_menu_keyboard():
    """Клавиатура главного меню пользователя"""
    keyboard = [
        [InlineKeyboardButton("📝 Пройти тест", callback_data="take_test")],
        [InlineKeyboardButton("📞 Поддержка", callback_data="support")],
        [InlineKeyboardButton("ℹ️ О боте", callback_data="about_bot")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Регистрация
def get_registration_skip_keyboard():
    """Клавиатура для пропуска шага регистрации"""
    keyboard = [
        [InlineKeyboardButton("⏭️ Пропустить", callback_data="skip_registration")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Выбор категории для теста
def get_categories_keyboard(categories):
    """Клавиатура выбора категории"""
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"📂 {category['name']}",
                callback_data=f"category_{category['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_to_menu")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Выбор теста
def get_tests_keyboard(tests):
    """Клавиатура выбора теста"""
    keyboard = []
    for test in tests:
        keyboard.append([
            InlineKeyboardButton(
                f"📋 {test['title']}",
                callback_data=f"test_{test['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ Назад к категориям", callback_data="back_to_categories")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Ответы на вопрос
def get_answers_keyboard(answers, question_id):
    """Клавиатура с вариантами ответов"""
    keyboard = []
    for answer in answers:
        keyboard.append([
            InlineKeyboardButton(
                f"✅ {answer['answer_text']}" if answer['is_correct'] else answer['answer_text'],
                callback_data=f"answer_{question_id}_{answer['id']}"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Результаты теста
def get_test_results_keyboard():
    """Клавиатура после завершения теста"""
    keyboard = [
        [InlineKeyboardButton("📊 Посмотреть результаты", callback_data="view_detailed_results")],
        [InlineKeyboardButton("🔄 Пройти другой тест", callback_data="take_another_test")],
        [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Детальные результаты
def get_detailed_results_keyboard():
    """Клавиатура детальных результатов"""
    keyboard = [
        [InlineKeyboardButton("🔄 Пройти тест заново", callback_data="retake_test")],
        [InlineKeyboardButton("📝 Пройти другой тест", callback_data="take_another_test")],
        [InlineKeyboardButton("⬅️ В главное меню", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# ========================= АДМИН ПАНЕЛЬ =========================

# Главное меню админа
def get_admin_main_keyboard():
    """Клавиатура главного меню админа"""
    keyboard = [
        [InlineKeyboardButton("📝 Управление тестами", callback_data="admin_tests")],
        [InlineKeyboardButton("📂 Управление категориями", callback_data="admin_categories")],
        [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🚫 Блокировка пользователей", callback_data="admin_block_users")],
        [InlineKeyboardButton("⬅️ Выйти из админки", callback_data="exit_admin")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Управление категориями
def get_admin_categories_keyboard(categories):
    """Клавиатура управления категориями"""
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"📂 {category['name']}",
                callback_data=f"admin_edit_category_{category['id']}"
            ),
            InlineKeyboardButton(
                "🗑️",
                callback_data=f"admin_delete_category_{category['id']}"
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("➕ Добавить категорию", callback_data="admin_add_category")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_main")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Управление тестами
def get_admin_tests_keyboard(tests):
    """Клавиатура управления тестами"""
    keyboard = []
    for test in tests:
        keyboard.append([
            InlineKeyboardButton(
                f"📋 {test['title']}",
                callback_data=f"admin_edit_test_{test['id']}"
            ),
            InlineKeyboardButton(
                "🗑️",
                callback_data=f"admin_delete_test_{test['id']}"
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("➕ Добавить тест", callback_data="admin_add_test")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_main")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Выбор категории для добавления теста
def get_admin_category_selection_keyboard(categories):
    """Клавиатура выбора категории для теста"""
    keyboard = []
    for category in categories:
        keyboard.append([
            InlineKeyboardButton(
                f"📂 {category['name']}",
                callback_data=f"admin_select_category_{category['id']}"
            )
        ])

    keyboard.append([
        InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_tests")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Управление вопросами в тесте
def get_admin_questions_keyboard(questions, test_id):
    """Клавиатура управления вопросами"""
    keyboard = []
    for question in questions:
        keyboard.append([
            InlineKeyboardButton(
                f"❓ {question['question_text'][:50]}...",
                callback_data=f"admin_edit_question_{question['id']}"
            ),
            InlineKeyboardButton(
                "🗑️",
                callback_data=f"admin_delete_question_{question['id']}"
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("➕ Добавить вопрос", callback_data=f"admin_add_question_{test_id}")],
        [InlineKeyboardButton("⬅️ Назад к тестам", callback_data="admin_back_to_tests")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Управление ответами на вопрос
def get_admin_answers_keyboard(answers, question_id):
    """Клавиатура управления ответами"""
    keyboard = []
    for answer in answers:
        status = "✅" if answer['is_correct'] else "❌"
        keyboard.append([
            InlineKeyboardButton(
                f"{status} {answer['answer_text'][:30]}...",
                callback_data=f"admin_edit_answer_{answer['id']}"
            ),
            InlineKeyboardButton(
                "🗑️",
                callback_data=f"admin_delete_answer_{answer['id']}"
            )
        ])

    keyboard.extend([
        [InlineKeyboardButton("➕ Добавить ответ", callback_data=f"admin_add_answer_{question_id}")],
        [InlineKeyboardButton("⬅️ Назад к вопросам", callback_data=f"admin_back_to_questions_{question_id}")]
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Статистика
def get_admin_stats_keyboard():
    """Клавиатура выбора периода статистики"""
    keyboard = [
        [InlineKeyboardButton("📊 За неделю", callback_data="stats_week")],
        [InlineKeyboardButton("📊 За месяц", callback_data="stats_month")],
        [InlineKeyboardButton("📊 За год", callback_data="stats_year")],
        [InlineKeyboardButton("📊 Общая статистика", callback_data="stats_all")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Блокировка пользователей
def get_admin_user_actions_keyboard(user_info):
    """Клавиатура действий с пользователем"""
    user_id = user_info['userId']
    is_blocked = user_info['isBlocked']

    if is_blocked:
        action_button = InlineKeyboardButton("🔓 Разблокировать", callback_data=f"admin_unblock_user_{user_id}")
    else:
        action_button = InlineKeyboardButton("🚫 Заблокировать", callback_data=f"admin_block_user_{user_id}")

    keyboard = [
        [action_button],
        [InlineKeyboardButton("👑 Назначить админом", callback_data=f"admin_make_admin_{user_id}")],
        [InlineKeyboardButton("⬅️ Назад", callback_data="admin_back_to_block_users")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Подтверждение действий
def get_confirmation_keyboard(action, data):
    """Клавиатура подтверждения действия"""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{action}_{data}")],
        [InlineKeyboardButton("❌ Отмена", callback_data=f"cancel_{action}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
